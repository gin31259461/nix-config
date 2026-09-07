# Independent source fixture: do not import the operator's configuration entry.
{ lib, ... }:
{
  networking.hostName = lib.mkDefault "fixture";
  networking.hotspot = lib.mapAttrs (_: lib.mkDefault) {
    connection = "fixture-ap";
    ssid = "Fixture";
    interface = "wifi0";
    uplink = "eth0";
    channel = 36;
    address = "192.0.2.1/24";
  };
  deployment.username = "abnertu";
  hardware.initramfs.images = [ "/boot/initramfs-linux.img" ];
  users.users.abnertu = {
    description = "Fixture login";
    homeDirectory = "/home/fixture";
    stateVersion = "26.05";
    admin = true;
    homeModules = [ ./home.nix ];
  };
  services.gitlabRunner.instances = import ../../modules/gitlab-runner/tests/instances.nix;
}
