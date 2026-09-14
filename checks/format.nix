{ lib, pkgs, pythonRuntime }:
let
  source = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../configuration.nix
      ../flake.nix
      ../pyproject.toml
      ../uv.lock
      ../lib
      ../hosts
      ../homes
      ../profiles
      ../platforms
      ../modules
      ../checks
    ];
  };
in
pkgs.runCommand "source-format-check"
  {
    nativeBuildInputs = [
      pkgs.nixfmt
      pkgs.ruff
      pkgs.pyright
      pkgs.shellcheck
      pkgs.findutils
    ];
  }
  ''
    find ${source} -name '*.nix' -print0 | xargs -0 nixfmt --check
    ruff check --no-cache --select F ${source}
    ruff format --no-cache --check ${source}
    shellcheck -x -e SC2154 ${source}/platforms/arch/arch-switch.sh
    cd ${source}
    pyright platforms/arch/system/model.py
    ${pythonRuntime}/bin/python -c 'import tomli_w'
    touch "$out"
  ''
