{
  pkgs,
  adapterPython ? pkgs.python3,
}:
let
  renderer = pkgs.writeShellScriptBin "progress-renderer" ''
    exec ${adapterPython}/bin/progress-renderer "$@"
  '';
in
{
  inherit renderer;
  python = adapterPython;
  pythonPath = ./.;
  shell = ''
    readonly progress_renderer=${renderer}/bin/progress-renderer
    readonly progress_base64=${pkgs.coreutils}/bin/base64
  ''
  + builtins.readFile ./progress.sh;
}
