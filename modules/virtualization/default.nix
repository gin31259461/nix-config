{ lib, config }:
{
  requiredPackages =
    lib.optionals (config.enable && config.kvm.enable) (import ./packages.nix).kvm
    ++ lib.optionals (config.enable && config.podman.enable) (import ./packages.nix).podman;
  loginGroups = lib.optional (config.enable && config.kvm.enable) "kvm";
}
