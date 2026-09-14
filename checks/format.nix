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
      pkgs.diffutils
    ];
  }
  ''
    formatted="$TMPDIR/formatted"
    cp -R ${source} "$formatted"
    chmod -R u+w "$formatted"
    find "$formatted" -name '*.nix' -print0 | xargs -0 nixfmt
    diff -ru ${source} "$formatted"
    cd ${source}
    ruff check --no-cache .
    ruff format --no-cache --check .
    shellcheck -x -e SC2154 platforms/arch/arch-switch.sh
    pyright
    ${pythonRuntime}/bin/python -c 'import tomli_w'
    touch "$out"
  ''
