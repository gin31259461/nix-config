{ pkgs, activationPackage }:
pkgs.writeShellApplication {
  name = "home-switch";
  text = ''
    readonly activation_package=${activationPackage}
  ''
  + builtins.readFile ./switch.sh;
}
