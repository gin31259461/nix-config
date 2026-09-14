{ pkgs, pythonRuntime }:
pkgs.runCommand "noctalia-config-tests" { } ''
  ${pythonRuntime}/bin/python ${./tests/test_sync.py} ${./sync.py}
  touch "$out"
''
