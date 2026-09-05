{
  lib,
  pkgs,
  rawInstances ? { },
}:
let
  enabled = rawInstances != { };
  instances = import ./interface.nix { inherit lib rawInstances; };
  platform = import ./arch-platform.nix;
  controller = import ./package.nix { inherit pkgs instances platform; };
  fixtures = import ./interface.nix {
    inherit lib;
    rawInstances = import ./tests/instances.nix;
  };
in
{
  requiredPackages = lib.optionals enabled (import ./packages.nix);
  packages = lib.optionalAttrs enabled { runnerctl = controller; };
  apps = lib.optionalAttrs enabled {
    runnerctl = {
      type = "app";
      program = "${controller}/bin/runnerctl";
      meta.description = "Manage dedicated rootless GitLab Runner instances";
    };
  };
  checks = {
    gitlab-runner-interface =
      assert import ./tests/interface.nix { inherit lib; };
      pkgs.writeText "gitlab-runner-interface" "passed";
    gitlab-runner-tests =
      pkgs.runCommand "gitlab-runner-tests" { nativeBuildInputs = [ pkgs.python3 ]; }
        ''
          python ${./tests}/test_runnerctl.py ${
            pkgs.writeText "runner-test-config.json" (
              builtins.toJSON {
                instances = fixtures;
                inherit platform;
              }
            )
          } ${./.}/runnerctl.py
          touch "$out"
        '';
  }
  // lib.optionalAttrs enabled {
    gitlab-runner-config = pkgs.runCommand "gitlab-runner-config-check" { } ''
      ${controller}/bin/runnerctl validate > "$out"
    '';
  };
}
