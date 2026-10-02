{ pkgs, adapterPython }:
pkgs.runCommand "noctalia-config-tests" { } ''
  ${adapterPython}/bin/python ${./tests/test_sync.py} ${./builtin-palettes.json} ${./sync.py}
  touch "$out"
''
