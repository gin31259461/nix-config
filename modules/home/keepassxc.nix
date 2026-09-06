{ config, lib, ... }:
let
  databaseFile = config.workstation.keepassxc.databaseFile;
  # systemd quoting, specifiers and environment expansion are not shell quoting.
  quotedDatabase =
    builtins.replaceStrings [ "\\" "\"" "%" "$" ] [ "\\\\" "\\\"" "%%" "$$" ]
      databaseFile;
in
{
  options.workstation.keepassxc.databaseFile = lib.mkOption {
    type = lib.types.str;
    description = "Absolute runtime database filename; never a Nix path or database contents.";
  };

  config = {
    assertions = [
      {
        assertion =
          lib.hasPrefix "/" databaseFile
          && !(lib.hasInfix "\n" databaseFile)
          && !(lib.hasInfix "\r" databaseFile);
        message = "KeePassXC databaseFile must be an absolute, single-line runtime filename.";
      }
    ];

    # Load the database without supplying a password. Consumers must not wait
    # for an unlocked collection, and tray recovery must never restart the vault.
    systemd.user.services.keepassxc = {
      Unit = {
        Description = "KeePassXC locked database and Secret Service provider";
        After = [
          "graphical-session.target"
          "noctalia.service"
        ];
        PartOf = [ "graphical-session.target" ];
        ConditionEnvironment = [ "WAYLAND_DISPLAY" ];
      };
      Service = {
        # A simple shell unit is started before its D-Bus tray is ready. Wait
        # for a host, but still allow manual vault access if the tray is absent.
        ExecStartPre = ''
          /usr/bin/bash -c 'deadline=$$((SECONDS + 10)); while (( SECONDS < deadline )); do ready=$$(/usr/bin/busctl --user --timeout=1s get-property org.kde.StatusNotifierWatcher /StatusNotifierWatcher org.kde.StatusNotifierWatcher IsStatusNotifierHostRegistered 2>/dev/null) && [[ "$$ready" == "b true" ]] && exit 0; /usr/bin/sleep 0.1; done; exit 0'
        '';
        TimeoutStartSec = "15s";
        ExecStart = ''/usr/bin/keepassxc --minimized "${quotedDatabase}"'';
        Restart = "no";
        Slice = "app-graphical.slice";
        TimeoutStopSec = "10s";
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
