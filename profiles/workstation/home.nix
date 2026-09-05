{ ... }:
{
  imports = [ ../../modules/home/config-files.nix ];

  home.sessionVariables = {
    QT_IM_MODULE = "fcitx";
    XMODIFIERS = "@im=fcitx";
  };
}
