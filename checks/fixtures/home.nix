{ config, lib, ... }:
{
  workstation.keepassxc.databaseFile = "${config.home.homeDirectory}/fixture.kdbx";
  workstation.noctalia.preferencesFile = ./noctalia.toml;
  programs.git.settings.user.name = lib.mkDefault "Fixture";
}
