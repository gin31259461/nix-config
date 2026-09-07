{ lib, pkgs }:
let
  parse = raw: import ../../../../lib/system-settings.nix { inherit lib raw; };
  valid = raw: (builtins.tryEval (builtins.deepSeq (parse raw) true)).success;
  baseline = parse (import ../../../../hosts/arch/system.nix);
  packages = import ../../packages.nix {
    inherit lib;
    systemSettings = baseline;
    hardware = {
      graphics = "generic";
      openrazer = false;
    };
  };
  optional = import ../default.nix {
    inherit lib pkgs;
    hostName = "fixture";
    config = parse {
      timeSync.servers = [ "ntp.example.test" ];
      journal = {
        storage = "persistent";
        systemMaxUseMiB = 1024;
        maxRetentionDays = 30;
      };
      power.powerKey = "ignore";
    };
  };

in
assert optional.files.timesyncd == "[Time]\nNTP=ntp.example.test\n";
assert
  optional.files.journald
  == "[Journal]\nMaxRetentionSec=30day\nStorage=persistent\nSystemMaxUse=1024M\n";
assert optional.files.logind == "[Login]\nHandlePowerKey=ignore\n";
assert valid { };
assert (parse { }).locale == null && (parse { }).firewall == null;
assert baseline.timeSync == null && baseline.journal == null && baseline.trim == null;
assert valid {
  locale = {
    generated = [ "en_US.UTF-8" ];
    lang = "en_US.UTF-8";
  };
};
assert valid {
  timeSync = { };
  journal.storage = "auto";
  console.keymap = "us";
  power.powerKey = "ignore";
  trim = { };
};
assert lib.all (value: !(valid value)) [
  { unknown = true; }
  {
    locale = {
      generated = [ "en_US.UTF-8" ];
      lang = "zh_TW.UTF-8";
    };
  }
  {
    locale = {
      generated = [ "C" ];
      lang = "C";
    };
  }
  { timeZone = "../../secret"; }
  { timeZone = "/etc/localtime"; }
  { timeZone = "Asia/Taipei\n"; }
  { timeSync.provider = "chrony"; }
  { timeSync.servers = [ "$(secret)" ]; }
  {
    journal = {
      storage = "auto";
      systemMaxUseMiB = 0;
    };
  }
  {
    journal = {
      storage = "auto";
      maxRetentionDays = -1;
    };
  }
  { console.keymap = "../us"; }
  { power = { }; }
  { trim.enable = false; }
  {
    firewall.rules = [
      {
        protocol = "tcp";
        fromPort = 0;
      }
    ];
  }
  {
    firewall.rules = [
      {
        protocol = "tcp";
        fromPort = 22;
        toPort = 1;
      }
    ];
  }
  { firewall.incoming = "allow"; }
  { firewall.command = "ufw reset"; }
];
assert builtins.elem "glibc" packages.pacman;
assert builtins.elem "ufw" packages.pacman;
assert builtins.elem "tzdata" packages.pacman;
true
