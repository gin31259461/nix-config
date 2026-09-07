{ lib }:
let
  inherit (lib) mkOption types;
  nullable =
    type:
    mkOption {
      type = types.nullOr type;
      default = null;
    };
  enum = types.enum;
  bounded = low: high: types.ints.between low high;
  token = types.strMatching "[a-zA-Z0-9_+-]+";
  localeName = enum [
    "en_US.UTF-8"
    "zh_TW.UTF-8"
  ];
  section = options: types.submodule { inherit options; };
  port = bounded 1 65535;
in
{
  locale = nullable (section {
    generated = mkOption { type = types.nonEmptyListOf localeName; };
    lang = mkOption { type = localeName; };
  });
  timeZone = nullable (types.strMatching "[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*");
  hostname.enable = lib.mkEnableOption "realizing Host identity as the static hostname";
  timeSync = nullable (section {
    provider = mkOption {
      type = enum [ "systemd-timesyncd" ];
      default = "systemd-timesyncd";
    };
    servers = mkOption {
      type = types.listOf (types.strMatching "[A-Za-z0-9][A-Za-z0-9.:-]*");
      default = [ ];
    };
  });
  journal = nullable (section {
    storage = mkOption {
      type = enum [
        "auto"
        "persistent"
        "volatile"
      ];
    };
    systemMaxUseMiB = nullable (bounded 1 1048576);
    systemKeepFreeMiB = nullable (bounded 1 1048576);
    runtimeMaxUseMiB = nullable (bounded 1 1048576);
    maxRetentionDays = nullable (bounded 1 3650);
  });
  console = nullable (section {
    keymap = mkOption { type = token; };
    font = nullable token;
  });
  power = nullable (section {
    powerKey = nullable (enum [
      "ignore"
      "poweroff"
      "suspend"
    ]);
    lidSwitch = nullable (enum [
      "ignore"
      "suspend"
    ]);
  });
  trim = nullable (section {
    enable = mkOption {
      type = enum [ true ];
      default = true;
    };
  });
  firewall = nullable (section {
    provider = mkOption {
      type = enum [ "ufw" ];
      default = "ufw";
    };
    incoming = mkOption {
      type = enum [ "deny" ];
      default = "deny";
    };
    outgoing = mkOption {
      type = enum [ "allow" ];
      default = "allow";
    };
    routed = mkOption {
      type = enum [ "deny" ];
      default = "deny";
    };
    logging = mkOption {
      type = enum [
        "off"
        "low"
        "medium"
        "high"
        "full"
      ];
      default = "low";
    };
    rules = mkOption {
      type = types.listOf (section {
        protocol = mkOption {
          type = enum [
            "tcp"
            "udp"
          ];
        };
        fromPort = mkOption { type = port; };
        toPort = nullable port;
      });
      default = [ ];
    };
  });
}
