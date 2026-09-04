{ ... }:
{
  imports = [ ../../modules/home/static-config.nix ];

  home.sessionVariables = {
    QT_IM_MODULE = "fcitx";
    XMODIFIERS = "@im=fcitx";
  };
}
