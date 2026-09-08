{
  lib,
  hardware,
  capabilities ? import ../../lib/default-capabilities.nix,
  modulePackages ? [ ],
  aiPackages ? [ ],
  aiVulkan ? false,
  aiProxy ? false,
  systemSettings ? { },
  moduleAurPackages ? [ ],
}:
{
  pacman = lib.unique (
    [
      "base-devel"
      "ca-certificates"
      "ca-certificates-utils"
      "coreutils"
      "curl"
      "dnsmasq"
      "hostapd"
      "i2c-tools"
      "inxi"
      "iproute2"
      "libnewt"
      "libva-utils"
      "linux-headers"
      "mtr"
      "nvtop"
      "pacman-contrib"
      "p11-kit"
      "procps-ng"
      "realtime-privileges"
      "rt-tests"
      "rtirq"
      "schedtool"
      "shadow"
      "systemd"
      "tuna"
      "util-linux"
      "vulkan-tools"
      "yt-dlp"
      "zsh"
    ]
    ++ lib.optionals capabilities.networking [
      "network-manager-applet"
      "networkmanager"
      "networkmanager-openconnect"
      "networkmanager-openvpn"
      "nm-connection-editor"
    ]
    ++ lib.optionals capabilities.bluetooth [
      "bluez"
      "bluez-utils"
      "blueman"
    ]
    ++ lib.optionals capabilities.power [
      "power-profiles-daemon"
    ]
    ++ lib.optionals capabilities.tailscale [
      "tailscale"
    ]
    ++ lib.optionals capabilities.desktop.enable [
      "adobe-source-code-pro-fonts"
      "adw-gtk-theme"
      "adwaita-cursors"
      "adwaita-fonts"
      "adwaita-icon-theme"
      "baobab"
      "brightnessctl"
      "cliphist"
      "ddcutil"
      "fcitx5"
      "fcitx5-chewing"
      "fcitx5-configtool"
      "fcitx5-gtk"
      "fcitx5-qt"
      "ffmpegthumbnailer"
      "freerdp"
      "ghostty"
      "gimp"
      "grim"
      "gvfs"
      "gvfs-mtp"
      "hyprland"
      "noctalia"
      "hypridle"
      "hyprlock"
      "hyprpolkitagent"
      "hyprsunset"
      "imagemagick"
      "inter-font"
      "keepassxc"
      "kitty"
      "libnotify"
      "loupe"
      "kvantum"
      "kvantum-qt5"
      "mpv"
      "noto-fonts"
      "noto-fonts-emoji"
      "nwg-displays"
      "nwg-look"
      "obs-studio"
      "obsidian"
      "otf-font-awesome"
      "papirus-icon-theme"
      "pavucontrol"
      "pipewire"
      "pipewire-alsa"
      "pipewire-audio"
      "pipewire-pulse"
      "playerctl"
      "qalculate-gtk"
      "qt5ct"
      "qt6-5compat"
      "qt6ct"
      "quickshell"
      "slurp"
      "swappy"
      "thunar"
      "thunar-archive-plugin"
      "thunar-volman"
      "ttf-droid"
      "ttf-fantasque-nerd"
      "ttf-fira-code"
      "ttf-firacode-nerd"
      "ttf-jetbrains-mono"
      "ttf-jetbrains-mono-nerd"
      "tumbler"
      "uwsm"
      "vlc"
      "wireplumber"
      "wl-clipboard"
      "xarchiver"
      "xdotool"
      "xdg-desktop-portal-gtk"
      "xdg-desktop-portal-hyprland"
      "xdg-user-dirs"
      "yad"
    ]
    ++ lib.optionals ((systemSettings.hotspot or null) != null) [ "iw" ]
    ++ lib.optionals ((systemSettings.firewall or null) != null) [ "ufw" ]
    ++ lib.optionals (hardware.graphics == "amd") [
      "amd-ucode"
      "amdgpu_top"
      "lib32-vulkan-radeon"
      "vulkan-radeon"
    ]
    ++ lib.optionals hardware.openrazer [
      "openrazer-daemon"
      "openrazer-driver-dkms"
    ]
    ++ lib.optionals ((systemSettings.locale or null) != null) [ "glibc" ]
    ++ lib.optionals ((systemSettings.timeZone or null) != null) [ "tzdata" ]
    ++ lib.optionals ((systemSettings.console or null) != null) [ "kbd" ]
    ++ modulePackages
    ++ aiPackages
    ++ lib.optional aiVulkan "ollama-vulkan"
    ++ lib.optional aiProxy "caddy"
  );

  lizardbyte = lib.optional (
    capabilities.desktop.enable && capabilities.programs.sunshine.enable
  ) "sunshine";

  aur =
    lib.optionals capabilities.desktop.enable [
      "bibata-cursor-theme-bin"
      "mpv-mpris"
      "mpvpaper"
      "noto-fonts-tc-vf"
      "obs-pipewire-audio-capture"
      "onedrive-abraunegg"
      "onlyoffice-bin"
      "powerpanel"
      "ttf-victor-mono"
      "zen-browser-bin"
    ]
    ++ lib.optional (capabilities.desktop.enable && capabilities.programs.vesktop.enable) "vesktop-bin"
    ++ lib.optional (capabilities.desktop.enable && capabilities.programs.vicinae.enable) "vicinae-bin"
    ++ lib.optional hardware.openrazer "polychromatic"
    ++ moduleAurPackages;
}
