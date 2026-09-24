{
  pkgs,
  instances,
  platform ? import ./arch-platform.nix,
  progress ? import ../../lib/cli/progress { inherit pkgs; },
}:
let
  manifestInstances = import ./render-artifacts.nix { inherit platform instances; };
  config = pkgs.writeText "gitlab-runner-instances.json" (
    builtins.toJSON {
      instances = manifestInstances;
      inherit platform;
    }
  );
in
pkgs.writeShellApplication {
  name = "runnerctl";
  runtimeInputs = [ progress.python ];
  text = ''
    export PYTHONPATH=${progress.pythonPath}
    exec ${progress.python}/bin/python ${./.}/runnerctl.py --config ${config} "$@"
  '';
}
