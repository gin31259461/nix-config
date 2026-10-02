{
  pkgs,
  instances,
  platform ? import ./arch-platform.nix,
  adapterPython ? pkgs.python3,
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
  runtimeInputs = [ adapterPython ];
  text = ''
    exec ${adapterPython}/bin/python ${./.}/runnerctl.py --config ${config} "$@"
  '';
}
