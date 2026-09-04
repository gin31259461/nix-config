{ platform, ... }:
let
  systemBin = if platform == "arch" then "/usr/bin" else "/run/current-system/sw/bin";
  bin = name: "${systemBin}/${name}";
  hyprpolkitagentExecutable =
    if platform == "arch" then
      "/usr/lib/hyprpolkitagent/hyprpolkitagent"
    else
      "${systemBin}/hyprpolkitagent";
  graphicalUnit = {
    After = [ "graphical-session.target" ];
    PartOf = [ "graphical-session.target" ];
    ConditionEnvironment = [ "WAYLAND_DISPLAY" ];
  };
  trayConsumerUnit = graphicalUnit // {
    After = [
      "graphical-session.target"
      "noctalia.service"
    ];
    Wants = [ "noctalia.service" ];
  };
  waitForStatusNotifierWatcher = ''
    ${bin "bash"} -c 'for _ in {1..100}; do ${bin "busctl"} --user get-property org.kde.StatusNotifierWatcher /StatusNotifierWatcher org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems >/dev/null 2>&1 && exit 0; ${bin "sleep"} 0.1; done; exit 0'
  '';
  restartableService = {
    Restart = "on-failure";
    RestartSec = "2s";
    TimeoutStopSec = "5s";
  };
in
{
  systemd.user = {
    startServices = "suggest";

    services = {
      hyprpolkitagent = {
        Unit = graphicalUnit // {
          Description = "Hyprland Polkit authentication agent";
        };
        Service = restartableService // {
          ExecStart = hyprpolkitagentExecutable;
          Slice = "session.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      vicinae = {
        Unit = trayConsumerUnit // {
          Description = "Vicinae launcher daemon";
          Documentation = [ "https://docs.vicinae.com" ];
          Requires = [ "dbus.socket" ];
        };
        Service = {
          Type = "simple";
          Environment = [ "VICINAE_OVERRIDES=%h/.config/vicinae/nix-managed.json" ];
          ExecStartPre = waitForStatusNotifierWatcher;
          ExecStart = "${bin "vicinae"} server --replace";
          ExecReload = "${bin "kill"} -HUP $MAINPID";
          KillMode = "process";
          Restart = "always";
          RestartSec = "60s";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      keepassxc = {
        Unit = graphicalUnit // {
          Description = "KeePassXC tray and Secret Service provider";
          Before = [
            "noctalia.service"
            "remmina-applet.service"
          ];
          ConditionPathExists = [
            "%h/.local/share/keepassxc/credentials.kdbx"
            "%h/.local/share/keepassxc/keepassxc-password.cred"
          ];
        };
        Service = {
          LoadCredentialEncrypted = "keepassxc-password:%h/.local/share/keepassxc/keepassxc-password.cred";
          ExecStart = ''
            ${bin "bash"} -c 'exec ${bin "keepassxc"} --minimized --pw-stdin "%h/.local/share/keepassxc/credentials.kdbx" < "%d/keepassxc-password"'
          '';
          ExecStartPost = ''
            ${bin "bash"} -c 'for _ in {1..150}; do ${bin "busctl"} --user get-property org.freedesktop.secrets /org/freedesktop/secrets/collection/credentials org.freedesktop.Secret.Collection Locked 2>/dev/null | ${bin "grep"} -qx "b false" && exit 0; ${bin "sleep"} 0.1; done; exit 1'
          '';
          Restart = "on-failure";
          RestartSec = "2s";
          Slice = "app-graphical.slice";
          TimeoutStartSec = "30s";
          TimeoutStopSec = "10s";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      keepassxc-tray-refresh = {
        Unit = graphicalUnit // {
          Description = "Refresh KeePassXC tray registration after Noctalia starts";
          After = [
            "keepassxc.service"
            "noctalia.service"
          ];
          ConditionPathExists = [ "%h/.local/share/keepassxc/credentials.kdbx" ];
        };
        Service = {
          Type = "oneshot";
          ExecStartPre = ''
            ${bin "bash"} -c 'for _ in {1..100}; do ${bin "busctl"} --user get-property org.kde.StatusNotifierWatcher /StatusNotifierWatcher org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems >/dev/null 2>&1 && ${bin "sleep"} 5 && exit 0; ${bin "sleep"} 0.1; done; exit 1'
          '';
          ExecStart = "${bin "systemctl"} --user --no-block restart keepassxc.service";
          RemainAfterExit = true;
          Slice = "session-graphical.slice";
          TimeoutStartSec = "20s";
        };
      };

      noctalia = {
        Unit = graphicalUnit // {
          Description = "Noctalia desktop shell";
          After = [
            "graphical-session.target"
            "keepassxc.service"
          ];
          Wants = [
            "keepassxc.service"
            "keepassxc-tray-refresh.service"
          ];
        };
        Service = restartableService // {
          ExecStart = bin "noctalia";
          Slice = "session-graphical.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      quickshell-overview = {
        Unit = graphicalUnit // {
          Description = "Quickshell workspace overview";
        };
        Service = restartableService // {
          ExecStart = "${bin "quickshell"} -c overview";
          Slice = "session-graphical.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      polychromatic-tray = {
        Unit = trayConsumerUnit // {
          Description = "Polychromatic tray applet";
          After = trayConsumerUnit.After ++ [ "openrazer-daemon.service" ];
          Wants = trayConsumerUnit.Wants ++ [ "openrazer-daemon.service" ];
        };
        Service = restartableService // {
          ExecStart = bin "polychromatic-tray-applet";
          Slice = "app-graphical.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      remmina-applet = {
        Unit = trayConsumerUnit // {
          Description = "Remmina tray applet";
        };
        Service = restartableService // {
          ExecStart = "${bin "remmina"} -i";
          Slice = "app-graphical.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      tailscale-systray = {
        Unit = trayConsumerUnit // {
          Description = "Tailscale systray";
        };
        Service = restartableService // {
          ExecStart = "${bin "tailscale"} systray";
          Slice = "app-graphical.slice";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };

      vesktop = {
        Unit = trayConsumerUnit // {
          Description = "Vesktop communication client";
        };
        Service = restartableService // {
          Environment = [ "ELECTRON_OZONE_PLATFORM_HINT=auto" ];
          ExecStartPre = "${bin "sleep"} 3";
          ExecStart = "${bin "vesktop"} --start-minimized --enable-features=UseOzonePlatform --ozone-platform-hint=wayland --enable-wayland-ime";
          RestartSec = "5s";
          Slice = "app-graphical.slice";
          TimeoutStopSec = "10s";
        };
        Install.WantedBy = [ "graphical-session.target" ];
      };
    };
  };

  xdg.configFile = {
    "vicinae/nix-managed.json".text = builtins.toJSON {
      providers.applications.entrypoints = {
        kitty.preferences.defaultAction = "launch";
        vesktop.preferences.defaultAction = "launch";
      };
    };
    "systemd/user/openrazer-daemon.service.d/delay.conf".text = ''
      [Service]
      ExecStartPre=${bin "sleep"} 20
    '';
    "systemd/user/sunshine.service.d/override.conf".text = ''
      [Service]
      Restart=on-failure
      RestartSec=5s

      [Install]
      WantedBy=graphical-session.target
    '';
  };
}
