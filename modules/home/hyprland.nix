{
  inputs,
  ...
}:
let
  uwsm = "/usr/bin/uwsm";
in
{
  imports = [ ./projection-safety.nix ];
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
