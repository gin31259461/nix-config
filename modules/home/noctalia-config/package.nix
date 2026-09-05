{
  pkgs,
  username,
  homeConfiguration,
}:
let
  python = pkgs.python3.withPackages (packages: [ packages.tomli-w ]);
in
pkgs.writeShellApplication {
  name = "noctalia-config";
  runtimeInputs = [
    pkgs.git
  ];
  text = ''
    exec ${python}/bin/python ${./sync.py} \
      --user ${pkgs.lib.escapeShellArg username} \
      --home-configuration ${pkgs.lib.escapeShellArg homeConfiguration} "$@"
  '';
}
