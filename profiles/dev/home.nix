{ pkgs, ... }:
{
  imports = [ ../../modules/home/neovim.nix ];

  home.packages = with pkgs; [
    git-credential-manager
    gnupg
    nodejs
    nix-output-monitor
  ];

  programs.password-store = {
    enable = true;
    package = pkgs.pass;
  };
}
