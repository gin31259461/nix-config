{ pkgs, ... }:
{
  imports = [ ../../modules/home/neovim.nix ];

  home.packages = with pkgs; [
    git-credential-manager
    gnupg
    nodejs
  ];

  programs.password-store = {
    enable = true;
    package = pkgs.pass;
  };
}
