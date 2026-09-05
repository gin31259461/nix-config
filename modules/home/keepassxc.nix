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
        After = [ "graphical-session.target" ];
        PartOf = [ "graphical-session.target" ];
        ConditionEnvironment = [ "WAYLAND_DISPLAY" ];
      };
      Service = {
        ExecStart = ''/usr/bin/keepassxc --minimized "${quotedDatabase}"'';
        Restart = "no";
        Slice = "app-graphical.slice";
        TimeoutStopSec = "10s";
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
