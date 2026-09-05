{
  lib,
  pkgs,
  inputs,
}:
let
  host = import ../lib/validate-host.nix {
    inherit lib;
    raw = (import ../hosts/arch) // {
      gitlabRunners = { };
      hardware = (import ../hosts/arch/hardware.nix) // {
        graphics = "generic";
        openrazer = false;
        initramfsModules = [
          "usbhid"
          "xhci_pci"
        ];
      };
    };
  };
  runners = import ../modules/gitlab-runner {
    inherit lib pkgs;
    rawInstances = host.gitlabRunners;
  };
  packages = import ../platforms/arch/packages.nix {
    inherit lib;
    inherit (host) hardware;
    modulePackages = runners.requiredPackages;
  };
  home = (import ../lib/mk-home-configuration.nix { inherit inputs; }) {
    inherit (host) system platform hardware;
    hostName = host.name;
    username = host.deployment.username;
    user = host.users.${host.deployment.username};
  };
  controller = import ../platforms/arch/package.nix {
    inherit lib pkgs packages;
    inherit (host) hardware;
    username = host.deployment.username;
    deploymentUser = host.users.${host.deployment.username};
  };
  homeWithoutKeePassXC = (import ../lib/mk-home-configuration.nix { inherit inputs; }) {
    inherit (host) system platform hardware;
    hostName = host.name;
    username = host.deployment.username;
    user = host.users.${host.deployment.username} // {
      modules = [ "graphical-session" ];
      # No user-specific database declaration when the capability is absent.
      homeModules = [ ];
    };
  };
in
assert runners.packages == { } && runners.apps == { };
assert !(builtins.elem "podman" packages.pacman);
assert !(builtins.elem "openrazer-daemon" packages.pacman);
assert !(builtins.elem "amd-ucode" packages.pacman);
assert !(builtins.hasAttr "polychromatic-tray" home.config.systemd.user.services);
assert !(builtins.hasAttr "keepassxc" homeWithoutKeePassXC.config.systemd.user.services);
assert
  !(builtins.elem "keepassxc.service" homeWithoutKeePassXC.config.systemd.user.services.noctalia.Unit.After);
pkgs.runCommand "optional-modules-check" { } ''
  test -x ${controller}/bin/arch-switch
  test -x ${home.activationPackage}/activate
  test -x ${homeWithoutKeePassXC.activationPackage}/activate
  touch "$out"
''
