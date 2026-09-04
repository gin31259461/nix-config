{
  inputs,
  platform,
  ...
}:
let
  uwsm = if platform == "arch" then "/usr/bin/uwsm" else "/run/current-system/sw/bin/uwsm";
in
{
  xdg.configFile."hypr" = {
    source = inputs.hypr-config;
    recursive = true;
  };

  home.file.".zprofile".text = ''
    if ${uwsm} check may-start; then
      exec ${uwsm} start hyprland.desktop
    fi
  '';
}
