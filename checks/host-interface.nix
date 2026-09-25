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
assert evaluate (
  builtins.removeAttrs raw [
    "gitlabRunners"
    "personalAgent"
    "systemSettings"
    "powerpanel"
  ]
);
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
assert evaluate (
  raw
  // {
    users = raw.users // {
      abnertu = raw.users.abnertu // {
        development = {
          neovimPath = "/home/abnertu/src/neovim";
          hyprlandPath = "/home/abnertu/src/hyprland";
        };
      };
    };
  }
);
assert
  !(evaluate (
    raw
    // {
      users = raw.users // {
        abnertu = raw.users.abnertu // {
          development = {
            neovimPath = "relative/path";
            hyprlandPath = null;
          };
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
          development = {
            neovimPath = null;
            hyprlandPath = 123;
          };
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
          development = {
            neovimPath = null;
            hyprlandPath = null;
            unknown = "invalid";
          };
        };
      };
    }
  ));
assert withoutRunners.packages == { };
assert withoutRunners.apps == { };
assert withoutRunners.requiredPackages == [ ];
true
