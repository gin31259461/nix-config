# Single entry point: imported values are defaults; ordinary definitions here win.
{ ... }:
{
  imports = [ ./hosts/arch ];

  # Example: networking.firewall.enable = false;
  # Example: users.users.abnertu.home.programs.git.settings.init.defaultBranch = "main";
}
