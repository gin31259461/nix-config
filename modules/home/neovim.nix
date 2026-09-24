{
  config,
  inputs,
  pkgs,
  user ? { },
  ...
}:
let
  neovimPath = user.development.neovimPath or null;
  targets = if neovimPath != null then [ ] else [ "nvim" ];
in
{
  imports = [
    (import ./projection-safety.nix {
      inherit targets;
      activationName = "checkNvimProjection";
    })
  ];
  xdg.configFile."nvim" =
    if neovimPath != null then
      {
        source = config.lib.file.mkOutOfStoreSymlink neovimPath;
      }
    else
      {
        source = inputs.nvim-config;
      };

  home.packages = with pkgs; [
    lazygit
    neovim
    tree-sitter
  ];
}
