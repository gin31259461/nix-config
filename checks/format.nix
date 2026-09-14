{
  lib,
  pkgs,
  pythonRuntime,
}:
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
    find ${source} -name '*.nix' -print0 | xargs -0 nixfmt --check
    cp -R ${source} "$TMPDIR/ruff-source"
    chmod -R u+w "$TMPDIR/ruff-source"
    cd "$TMPDIR/ruff-source"
    ruff check --no-cache --fix . || true
    diff -ru ${source} "$TMPDIR/ruff-source"
    exit 1
  ''
