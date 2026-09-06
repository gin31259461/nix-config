{ lib, pkgs }:
let
  raw = import ../hosts/arch;
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
assert lib.all
  (
    homeDirectory:
    !(evaluate (
      raw
      // {
        users = raw.users // {
          abnertu = raw.users.abnertu // {
            inherit homeDirectory;
          };
        };
      }
    ))
  )
  [
    "/home/"
    "/home/../outside"
    "/home/user/../other"
    "/home/user\n"
    "/home//user"
  ];
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
assert
  !(evaluate (
    raw
    // {
      users.abnertu = raw.users.abnertu // {
        description = 42;
      };
    }
  ));
assert evaluate (builtins.removeAttrs raw [ "gitlabRunners" ]);
assert !(evaluate (raw // { typo = true; }));
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
assert
  !(evaluate (
    raw
    // {
      users = raw.users // {
        abnertu = raw.users.abnertu // {
          modules = [ "unknown" ];
        };
      };
    }
  ));
assert withoutRunners.packages == { };
assert withoutRunners.apps == { };
assert withoutRunners.requiredPackages == [ ];
true
