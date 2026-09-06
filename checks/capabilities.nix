{
  lib,
  pkgs,
  inputs,
}:
let
  ai =
    raw:
    import ../modules/ai {
      inherit lib;
      config = import ../modules/ai/interface.nix { inherit lib raw; };
    };
  virtualization =
    raw:
    import ../modules/virtualization {
      inherit lib;
      config = import ../modules/virtualization/interface.nix { inherit lib raw; };
    };
  valid =
    name: raw:
    (builtins.tryEval (
      builtins.deepSeq (import (../modules + "/${name}/interface.nix") { inherit lib raw; }) true
    )).success;
  enabled = ai { enable = true; };
  disabled = ai { enable = false; };
  v = virtualization { enable = true; };
  gui = virtualization {
    enable = true;
    kvm.gui.enable = true;
  };
  host = import ../hosts/arch;
  home = (import ../lib/mk-home-configuration.nix { inherit inputs; }) {
    inherit (host)
      system
      platform
      hardware
      ai
      ;
    hostName = host.name;
    username = host.deployment.username;
    user = host.users.${host.deployment.username};
  };
  homeDisabled = (import ../lib/mk-home-configuration.nix { inherit inputs; }) {
    inherit (host) system platform hardware;
    ai.enable = false;
    hostName = host.name;
    username = host.deployment.username;
    user = host.users.${host.deployment.username};
  };
  native = import ../platforms/arch/packages.nix {
    inherit lib;
    inherit (host) hardware;
    modulePackages = v.requiredPackages;
    moduleAurPackages = enabled.aurPackages;
  };
  skills = lib.filterAttrs (name: _: lib.hasPrefix ".agents/skills/" name) home.config.home.file;
in
assert enabled.aurPackages == [ "openai-codex-bin" ];
assert disabled.aurPackages == [ ] && disabled.homeModule.home.file == { };
assert
  (ai {
    enable = true;
    codex.enable = false;
  }).aurPackages == [ ];
assert
  (ai {
    enable = true;
    skillsPresets.enable = false;
  }).homeModule.home.file == { };
assert (virtualization { }).requiredPackages == [ ];
assert (virtualization { enable = false; }).loginGroups == [ ];
assert builtins.elem "qemu-desktop" v.requiredPackages;
assert builtins.elem "podman" v.requiredPackages;
assert v.loginGroups == [ "kvm" ];
assert v.systemUnits == [ ];
assert !(builtins.elem "virt-manager" v.requiredPackages);
assert builtins.elem "virt-manager" gui.requiredPackages;
assert builtins.elem "libvirt" gui.requiredPackages;
assert gui.systemUnits == [ "libvirtd.socket" ];
assert gui.loginGroups == [ "kvm" ];
assert lib.all
  (
    raw:
    let
      disabledGui = virtualization raw;
    in
    disabledGui.systemUnits == [ ]
    && !(builtins.elem "virt-manager" disabledGui.requiredPackages)
    && !(builtins.elem "libvirt" disabledGui.requiredPackages)
  )
  [
    {
      enable = false;
      kvm.gui.enable = true;
    }
    {
      enable = true;
      kvm.enable = false;
      kvm.gui.enable = true;
    }
    {
      enable = true;
      kvm.gui.enable = false;
    }
  ];
assert !(valid "virtualization" { kvm.gui.enable = "true"; });
assert !(valid "virtualization" { kvm.gui.enabel = true; });
assert
  !(builtins.elem "podman"
    (virtualization {
      enable = true;
      podman.enable = false;
    }).requiredPackages
  );
assert
  (virtualization {
    enable = true;
    kvm.enable = false;
  }).loginGroups == [ ];
assert
  !(builtins.elem "qemu-desktop"
    (virtualization {
      enable = true;
      kvm.enable = false;
    }).requiredPackages
  );
assert lib.all (name: !(valid name { enable = "true"; }) && !(valid name { typo = true; })) [
  "ai"
  "virtualization"
];
assert !(valid "ai" { codex.enabel = true; });
assert !(valid "virtualization" { kvm.enabel = true; });
assert builtins.elem "openai-codex-bin" native.aur;
assert builtins.elem "qemu-desktop" native.pacman && builtins.elem "podman" native.pacman;
assert
  lib.filterAttrs (name: _: lib.hasPrefix ".agents/skills/" name) homeDisabled.config.home.file
  == { };
assert skills != { };
assert lib.all (file: !file.recursive) (builtins.attrValues skills);
pkgs.writeText "capabilities-check" "passed"
