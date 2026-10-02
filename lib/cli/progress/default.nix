{
  pkgs,
  adapterPython ? pkgs.python3,
}:
let
  renderer = pkgs.writeShellScriptBin "progress-renderer" ''
    if [ -x "${adapterPython}/bin/progress-renderer" ]; then
      exec ${adapterPython}/bin/progress-renderer "$@"
    else
      exit 1
    fi
  '';
in
{
  inherit renderer;
  shell = ''
    readonly progress_renderer=${renderer}/bin/progress-renderer
    readonly progress_base64=${pkgs.coreutils}/bin/base64
  ''
  + builtins.readFile ./progress.sh;
}
