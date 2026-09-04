{
  abnertu = {
    description = "Abner Tu";
    homeDirectory = "/home/abnertu";
    stateVersion = "26.05";
    admin = true;
    groups = [
      "i2c"
      "openrazer"
      "realtime"
    ];

    profiles = [
      "base"
      "dev"
      "workstation"
    ];
    modules = [
      "hyprland"
      "graphical-session"
    ];
    homeModules = [ ../../homes/abnertu/home.nix ];
  };
}
