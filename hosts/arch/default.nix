{
  name = "arch";
  platform = "arch";
  system = "x86_64-linux";
  deployment = {
    profile = "workstation";
    username = "abnertu";
  };
  ai = {
    enable = true;
    codex.enable = true;
    skillsPresets.enable = true;
  };
  virtualization = {
    enable = true;
    kvm.enable = true;
    kvm.gui.enable = true;
    podman.enable = true;
  };
  systemSettings = import ./system.nix;
  users = import ./users.nix;
  gitlabRunners = import ./gitlab-runners.nix;
  hardware = import ./hardware.nix;
}
