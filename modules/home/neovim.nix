{ inputs, pkgs, ... }:
{
  imports = [ ./projection-safety.nix ];
  xdg.configFile."nvim" = {
    source = inputs.neovim-config;
  };

  home.packages = with pkgs; [
    lazygit
    neovim
    tree-sitter
  ];
}
