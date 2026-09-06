{ config, ... }:
{
  workstation.keepassxc.databaseFile = "${config.home.homeDirectory}/.local/share/keepassxc/credentials.kdbx";
}
