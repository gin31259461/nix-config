{ lib, pkgs }:
let
  evaluated =
    (import ../lib/eval-configuration.nix {
      inherit lib;
      modules = [ ./fixtures/configuration.nix ];
    }).host;
  raw = evaluated // {
    users = lib.mapAttrs (_: user: builtins.removeAttrs user [ "homeConfig" ]) evaluated.users;
  };
  evaluate =
    value:
    (builtins.tryEval (
      builtins.deepSeq (import ../lib/validate-host.nix {
        inherit lib;
        raw = value;
      }) true
    )).success;
  withoutRunners = import ../modules/gitlab-runner { inherit lib pkgs; };
in
assert evaluate raw;
assert evaluate (
  raw
  // {
    users = raw.users // {
      fixture = raw.users.abnertu // {
        homeDirectory = "/home/team/fixture";
        description = "Fixture";
      };
    };
  }
);
assert
  !(evaluate (
    raw
    // {
      users = raw.users // {
        fixture = raw.users.abnertu;
      };
    }
  ));
assert evaluate (
  builtins.removeAttrs raw [
    "gitlabRunners"
    "systemSettings"
  ]
);
assert !(evaluate (raw // { typo = true; }));
assert
  !(evaluate (
    raw
    // {
      users.abnertu = raw.users.abnertu // {
        typo = true;
      };
    }
  ));
assert
  !(evaluate (
    raw
    // {
      deployment = raw.deployment // {
        username = "missing";
      };
    }
  ));
assert
  !(evaluate (
    raw
    // {
      users = raw.users // {
        abnertu = raw.users.abnertu // {
          admin = false;
        };
      };
    }
  ));
assert
  !(evaluate (
    raw
    // {
      users = raw.users // {
        abnertu = raw.users.abnertu // {
          profiles = [ "unknown" ];
        };
      };
    }
  ));
assert withoutRunners.packages == { };
assert withoutRunners.apps == { };
assert withoutRunners.requiredPackages == [ ];
true
