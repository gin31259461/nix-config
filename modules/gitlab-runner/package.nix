{
  pkgs,
  instances,
  platform ? import ./arch-platform.nix,
  progress ? import ../../lib/cli/progress { inherit pkgs; },
}:
let
  config = pkgs.writeText "gitlab-runner-instances.json" (
    builtins.toJSON { inherit instances platform; }
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
