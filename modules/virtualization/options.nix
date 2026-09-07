{ lib }:
{
  enable = (lib.mkEnableOption "virtualization") // {
    default = true;
  };
  kvm.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
  };
  kvm.gui.enable = (lib.mkEnableOption "virt-manager with local libvirt management") // {
    default = true;
  };
  podman.enable = lib.mkOption {
    type = lib.types.bool;
    default = true;
  };
}
