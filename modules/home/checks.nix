{
  pkgs,
  home,
  inputs,
}:
let
  lib = pkgs.lib;
  fixture =
    full:
    (import ../../lib/mk-home-configuration.nix { inherit inputs; }) {
      system = pkgs.stdenv.hostPlatform.system;
      hostName = "fixture";
      platform = "arch";
      hardware = {
        graphics = "generic";
        openrazer = full;
      };
      username = if full then "tester" else "second";
      user = {
        homeDirectory = if full then "/home/tester" else "/home/team/second";
        stateVersion = "26.05";
        profiles = [ ];
        modules = [
          "graphical-session"
        ]
        ++ lib.optionals full [
          "keepassxc"
          "noctalia-storage"
        ];
        homeModules = lib.optional full ./tests/session-home.nix;
      };
    };
  sessionFixture =
    full:
    let
      generated = fixture full;
    in
    {
      units = "${generated.activationPackage}/home-files/.config/systemd/user";
      expected = pkgs.writeText "session-expectations.json" (
        builtins.toJSON {
          home = generated.config.home.homeDirectory;
          keepassxc = full;
          storage = full;
          openrazer = full;
        }
      );
    };
in
{
  overview-refresh = import ./overview/checks.nix { inherit pkgs; };
  noctalia-config = import ./noctalia-config/checks.nix { inherit pkgs; };
  noctalia-storage =
    pkgs.runCommand "noctalia-storage-check" { nativeBuildInputs = [ pkgs.python3 ]; }
      ''
        python ${./tests/test_noctalia_storage.py} ${./prepare-noctalia-storage.py}
        touch "$out"
      '';
  graphical-session-ordering =
    pkgs.runCommand "graphical-session-ordering"
      {
        nativeBuildInputs = [
          pkgs.python3
          pkgs.bash
          pkgs.coreutils
        ];
      }
      ''
        ${lib.concatMapStringsSep "\n"
          (
            full:
            let
              f = sessionFixture full;
            in
            "python ${./tests/test_session.py} ${f.units} ${f.expected}"
          )
          [
            true
            false
          ]
        }
        touch "$out"
      '';
  home-projection =
    pkgs.runCommand "home-projection-check"
      {
        nativeBuildInputs = [
          pkgs.python3
          pkgs.bash
          pkgs.coreutils
        ];
      }
      ''
        python ${./tests/test_projection.py} ${./check-projection.sh}
        touch "$out"
      '';
  home-projection-interface =
    assert pkgs.lib.hasInfix "exec /usr/bin/uwsm start hyprland.desktop"
      home.config.home.file.".zprofile".text;
    assert !home.config.xdg.configFile.nvim.recursive;
    assert home.config.xdg.configFile.hypr.recursive;
    assert builtins.all (
      name: !pkgs.lib.hasPrefix ".agents/skills/" name || !home.config.home.file.${name}.recursive
    ) (builtins.attrNames home.config.home.file);
    pkgs.writeText "home-projection-interface" "passed";
  arch-graphical-session = pkgs.runCommand "arch-graphical-session-check" { } ''
    units=${home.activationPackage}/home-files/.config/systemd/user
    profile=${home.config.home.path}
    for unit in \
      hyprpolkitagent.service \
      keepassxc.service \
      noctalia.service \
      polychromatic-tray.service \
      quickshell-overview.service \
      tailscale-systray.service \
      vesktop.service \
      vicinae.service; do
      [[ -f "$units/$unit" ]] || continue
      if ${pkgs.gnugrep}/bin/grep -Eq '^Exec(Start|StartPre|StartPost|Reload)=.*/nix/store/' "$units/$unit"; then
        printf 'Arch graphical unit references a Nix package: %s\n' "$unit" >&2
        exit 1
      fi
    done
    for unit in \
      polychromatic-tray.service \
      tailscale-systray.service \
      vesktop.service \
      vicinae.service; do
      [[ -f "$units/$unit" ]] || continue
      if ! ${pkgs.gnugrep}/bin/grep -qx 'After=noctalia.service' "$units/$unit"; then
        printf 'Tray consumer does not start after Noctalia: %s\n' "$unit" >&2
        exit 1
      fi
    done
    if ! ${pkgs.gnugrep}/bin/grep -q '^ExecStartPre=.*StatusNotifierWatcher' "$units/vicinae.service"; then
      printf 'Vicinae does not wait for Noctalia tray readiness\n' >&2
      exit 1
    fi
    if ! ${pkgs.gnugrep}/bin/grep -qx \
      'Environment=VICINAE_OVERRIDES=%h/.config/vicinae/nix-managed.json' \
      "$units/vicinae.service"; then
      printf 'Vicinae does not load the managed launcher policy\n' >&2
      exit 1
    fi
    for application in kitty vesktop; do
      if ! ${pkgs.gnugrep}/bin/grep -q \
        "\"$application\":{\"preferences\":{\"defaultAction\":\"launch\"}}" \
        "$units/../../vicinae/nix-managed.json"; then
        printf 'Vicinae does not launch a new %s instance by default\n' "$application" >&2
        exit 1
      fi
    done
    for executable in \
      ghostty \
      gimp \
      hypridle \
      hyprlock \
      hyprpolkitagent \
      hyprsunset \
      keepassxc \
      kitty \
      mpv \
      mpvpaper \
      noctalia \
      noctalia-shell \
      obs \
      quickshell \
      remmina \
      swappy \
      uwsm \
      vesktop \
      vicinae \
      vlc; do
      if [[ -e "$profile/bin/$executable" ]]; then
        printf 'Arch Home profile provides a native graphical executable: %s\n' "$executable" >&2
        exit 1
      fi
    done
    touch "$out"
  '';
}
