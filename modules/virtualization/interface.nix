{
  lib,
  raw ? { },
}:
let
  config = lib.evalModules {
    modules = [
      ({ lib, ... }: {
        options = {
          enable = lib.mkEnableOption "virtualization";
          kvm.enable = lib.mkOption {
            type = lib.types.bool;
            default = true;
          };
          kvm.gui.enable = lib.mkEnableOption "virt-manager with local libvirt management";
          podman.enable = lib.mkOption {
            type = lib.types.bool;
            default = true;
          };
        };
      })
      raw
    ];
  };
in
builtins.deepSeq config.config config.config
