{ config, lib, ... }:
{
  imports = [ ./system.nix ];
  networking.hostName = lib.mkDefault "arch";
  deployment.username = lib.mkDefault "abnertu";
  hardware = lib.mapAttrsRecursive (_: lib.mkDefault) (import ./hardware.nix);
  users.users = import ./users.nix { inherit config lib; };
  services.gitlabRunner.instances = lib.mapAttrs (
    _: value: lib.mapAttrsRecursive (_: lib.mkDefault) value
  ) (import ./gitlab-runners.nix);
}
