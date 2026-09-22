{ pkgs }:
let
  python = pkgs.python3.withPackages (packages: [ packages.rich ]);
  renderer = pkgs.writeShellScriptBin "progress-renderer" ''
    exec ${python}/bin/python ${./progress.py} "$@"
  '';
in
{
  inherit python renderer;
  pythonPath = ./.;
  shell = ''
    readonly progress_renderer=${renderer}/bin/progress-renderer
    readonly progress_base64=${pkgs.coreutils}/bin/base64
  ''
  + builtins.readFile ./progress.sh;
}
