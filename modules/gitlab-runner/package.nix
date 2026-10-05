{
  pkgs,
  instances,
  gitlab-runner ? null,
  platform ? import ./arch-platform.nix,
}:
let
  manifestInstances = import ./render-artifacts.nix { inherit platform instances; };
  config = pkgs.writeText "gitlab-runner-instances.json" (
    builtins.toJSON {
      instances = manifestInstances;
      inherit platform;
    }
  );
  runnerctlPackage =
    if gitlab-runner != null then
      gitlab-runner.packages.${pkgs.stdenv.hostPlatform.system}.default
    else
      pkgs.emptyFile;
in
pkgs.writeShellApplication {
  name = "runnerctl";
  runtimeInputs = [ runnerctlPackage ];
  text = ''
    exec runnerctl --config ${config} "$@"
  '';
}
