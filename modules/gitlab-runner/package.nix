{
  pkgs,
  instances,
  platform ? import ./arch-platform.nix,
}:
let
  config = pkgs.writeText "gitlab-runner-instances.json" (
    builtins.toJSON { inherit instances platform; }
  );
in
pkgs.writeShellApplication {
  name = "runnerctl";
  runtimeInputs = with pkgs; [
    python3
  ];
  text = ''
    exec python3 ${./runnerctl.py} --config ${config} "$@"
  '';
}
