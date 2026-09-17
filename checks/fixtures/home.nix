{ lib, ... }:
{
  workstation.noctalia.preferencesFile = ./noctalia.toml;
  programs.git.settings.user.name = lib.mkDefault "Fixture";
}
