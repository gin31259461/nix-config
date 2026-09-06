{ lib, config }:
let
  kvmEnabled = config.enable && config.kvm.enable;
  guiEnabled = kvmEnabled && config.kvm.gui.enable;
  packages = import ./packages.nix;
in
{
  requiredPackages =
    lib.optionals kvmEnabled packages.kvm
    ++ lib.optionals guiEnabled packages.gui
    ++ lib.optionals (config.enable && config.podman.enable) packages.podman;
  loginGroups = lib.optional kvmEnabled "kvm";
  systemUnits = lib.optional guiEnabled "libvirtd.socket";
}
