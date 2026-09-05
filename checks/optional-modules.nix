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
in
assert runners.packages == { } && runners.apps == { };
assert !(builtins.elem "podman" packages.pacman);
assert !(builtins.elem "openrazer-daemon" packages.pacman);
assert !(builtins.elem "amd-ucode" packages.pacman);
assert !(builtins.hasAttr "polychromatic-tray" home.config.systemd.user.services);
pkgs.runCommand "optional-modules-check" { } ''
  test -x ${controller}/bin/arch-switch
  test -x ${home.activationPackage}/activate
  touch "$out"
''
