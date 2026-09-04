{ pkgs, ... }:
{
  imports = [ ../../modules/home/neovim.nix ];

  home.packages = with pkgs; [
    git-credential-manager
    gnupg
    nodejs
    pass
  ];
}
