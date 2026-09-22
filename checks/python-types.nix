{ lib, pkgs }:
let
  python = pkgs.python3.withPackages (packages: [
    packages.tomli-w
    packages.rich
  ]);
  source = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../pyproject.toml
      ../checks
      ../lib
      ../modules
      ../platforms
    ];
  };
in
pkgs.runCommand "python-type-check"
  {
    nativeBuildInputs = [ pkgs.pyright ];
  }
  ''
    cd ${source}
    pyright --pythonpath ${python}/bin/python
    touch "$out"
  ''
