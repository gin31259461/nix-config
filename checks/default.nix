{
  pkgs,
  lib,
  arch-switch,
  archDeployment,
  deploymentName,
}:
{
  home-source-assets = import ./assets.nix { inherit pkgs; };
  host-interface =
    assert import ./host-interface.nix { inherit lib pkgs; };
    pkgs.writeText "host-interface" "passed";
  workflow = pkgs.runCommand "github-workflow-check" { nativeBuildInputs = [ pkgs.actionlint ]; } ''
    actionlint ${../.github/workflows/check.yml}
    touch "$out"
  '';
  deployment-ordering =
    pkgs.runCommand "deployment-ordering"
      {
        nativeBuildInputs = [
          pkgs.python3
          pkgs.bash
          pkgs.coreutils
        ];
      }
      ''
        python ${../lib/deployment/tests/test_deployment.py} ${../lib/deployment/deploy.sh} ${../lib/deployment/home/switch.sh}
        touch "$out"
      '';
  arch-switch-interface = pkgs.runCommand "arch-switch-interface-check" { } ''
    ${arch-switch}/bin/arch-switch --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: arch-switch [--check | --update] [--verbose]'
    if ${arch-switch}/bin/arch-switch --check --update >/dev/null 2>&1; then exit 1; fi
    ${archDeployment}/bin/${deploymentName} --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: ${deploymentName} [--update] [--verbose]'
    touch "$out"
  '';
  justfile =
    let
      fakeNix = pkgs.writeShellScriptBin "nix" ''
        printf '%s\n' "$*" >> "$JUST_NIX_LOG"
      '';
    in
    pkgs.runCommand "justfile-check"
      {
        nativeBuildInputs = [
          pkgs.bash
          pkgs.coreutils
          pkgs.just
          fakeNix
        ];
      }
      ''
        just --justfile ${../Justfile} --summary > "$out"
        grep -Fxq 'arch-workstation build check check-arch check-fast default initialize-runner prepare-ai prepare-runner status-runner verify-runner' "$out"

        export JUST_NIX_LOG="$TMPDIR/nix.log"
        run_recipe() {
          just --justfile ${../Justfile} --dry-run arch-workstation "$@" 2>&1 |
            tail -n +2 |
            bash
        }
        run_recipe verbose update
        grep -Fxq 'build --no-link --show-trace --print-build-logs --verbose .#arch-workstation' "$JUST_NIX_LOG"
        grep -Fxq 'run --show-trace --print-build-logs --verbose .#arch-workstation -- --update --verbose' "$JUST_NIX_LOG"

        : > "$JUST_NIX_LOG"
        run_recipe update verbose
        grep -Fxq 'run --show-trace --print-build-logs --verbose .#arch-workstation -- --update --verbose' "$JUST_NIX_LOG"

        : > "$JUST_NIX_LOG"
        run_recipe
        grep -Fxq 'build --no-link --show-trace --print-build-logs .#arch-workstation' "$JUST_NIX_LOG"
        grep -Fxq 'run --show-trace --print-build-logs .#arch-workstation' "$JUST_NIX_LOG"
        test "$(wc -l < "$JUST_NIX_LOG")" -eq 2

        : > "$JUST_NIX_LOG"
        if run_recipe update update; then exit 1; fi
        if run_recipe unknown; then exit 1; fi
        test ! -s "$JUST_NIX_LOG"
      '';
}
