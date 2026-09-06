{ ... }:
let
  sourceRoot = ../../files/home;
  configDirectories = [
    "Kvantum"
    "btop"
    "cava"
    "fastfetch"
    "ghostty"
    "gtk-3.0"
    "gtk-4.0"
    "kitty"
    "onedrive"
    "openrazer"
    "qt5ct"
    "qt6ct"
    "quickshell"
    "swappy"
    "vesktop/settings"
    "vesktop/themes"
  ];
in
{
  xdg.configFile =
    builtins.listToAttrs (
      map (name: {
        inherit name;
        value = {
          source = sourceRoot + "/.config/${name}";
          recursive = true;
        };
      }) configDirectories
    )
    // {
      "electron-flags.conf".source = sourceRoot + "/.config/electron-flags.conf";
      "polychromatic/preferences.json".source = sourceRoot + "/.config/polychromatic/preferences.json";
      "sunshine/sunshine.conf".source = sourceRoot + "/.config/sunshine/sunshine.conf";
      "vesktop/settings.json".source = sourceRoot + "/.config/vesktop/settings.json";
    };

  home.file = {
    "AGENTS.md".source = sourceRoot + "/AGENTS.md";
    ".p10k.zsh".source = sourceRoot + "/.p10k.zsh";
    "Pictures/Wallpapers" = {
      source = sourceRoot + "/Pictures/Wallpapers";
      recursive = true;
    };
  };
}
