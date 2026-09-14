{ inputs, pkgs, ... }:
{
  imports = [
    (import ./projection-safety.nix {
      targets = [ "nvim" ];
      activationName = "checkNvimProjection";
    })
  ];
  xdg.configFile."nvim" = {
    source = inputs.nvim-config;
  };

  home.packages = with pkgs; [
    lazygit
    neovim
    tree-sitter
  ];
}
