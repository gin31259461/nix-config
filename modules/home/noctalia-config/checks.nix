{ pkgs }:
let
  python = pkgs.python3.withPackages (packages: [ packages.tomli-w ]);
in
pkgs.runCommand "noctalia-config-tests" { } ''
  ${python}/bin/python ${./tests/test_sync.py} ${./builtin-palettes.json} ${./sync.py}
  touch "$out"
''
