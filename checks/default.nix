{
  pkgs,
  lib,
  arch-switch,
  archDeployment,
  deploymentName,
}:
let
  progress = import ../lib/cli/progress { inherit pkgs; };
in
{
  home-source-assets = import ./assets.nix { inherit pkgs; };
  host-interface =
    assert import ./host-interface.nix { inherit lib pkgs; };
    pkgs.writeText "host-interface" "passed";
  workflow = pkgs.runCommand "github-workflow-check" { nativeBuildInputs = [ pkgs.actionlint ]; } ''
    actionlint ${../.github/workflows/check.yml}
    touch "$out"
  '';
  progress-ui =
    pkgs.runCommand "progress-ui-tests"
      {
        nativeBuildInputs = [
          progress.python
          pkgs.bash
          pkgs.coreutils
        ];
      }
      ''
        export PYTHONPATH=${progress.pythonPath}
        python -m unittest discover -s ${progress.pythonPath}/tests -v
        python ${./tests/test_progress_contract.py} ${progress.pythonPath}
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
    ${arch-switch}/bin/arch-switch --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: arch-switch [--check | --update | --purge] [--verbose]'
    if ${arch-switch}/bin/arch-switch --check --update >/dev/null 2>&1; then exit 1; fi
    ${archDeployment}/bin/${deploymentName} --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: ${deploymentName} [--update] [--purge] [--verbose]'
    touch "$out"
  '';
  justfile =
    let
      source = lib.fileset.toSource {
        root = ../.;
        fileset = lib.fileset.unions [
          ../Justfile
          ../lib/cli/nix.sh
          ./tests/test_cli.py
        ];
      };
    in
    pkgs.runCommand "justfile-check"
      {
        nativeBuildInputs = [
          pkgs.bash
          pkgs.coreutils
          pkgs.just
          pkgs.python3
        ];
      }
      ''
        just --justfile ${source}/Justfile --summary > "$out"
        grep -Fxq 'arch-workstation build check check-arch check-fast default initialize-runner prepare-ai prepare-runner status-runner verify-runner' "$out"
        python ${source}/checks/tests/test_cli.py ${source}
      '';
}
