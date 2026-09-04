{
  name = "arch";
  platform = "arch";
  system = "x86_64-linux";
  deployment = {
    profile = "workstation";
    username = "abnertu";
  };
  users = import ./users.nix;
  gitlabRunners = import ./gitlab-runners.nix;
  systemPackages = import ./system-packages.nix;
}
