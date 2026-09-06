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
    ${arch-switch}/bin/arch-switch --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: arch-switch [--check | --update]'
    if ${arch-switch}/bin/arch-switch --check --update >/dev/null 2>&1; then exit 1; fi
    ${archDeployment}/bin/${deploymentName} --help | ${pkgs.gnugrep}/bin/grep -Fxq 'usage: ${deploymentName} [--update] [--verbose]'
    touch "$out"
  '';
  justfile =
    pkgs.runCommand "justfile-check"
      {
        nativeBuildInputs = [ pkgs.just ];
      }
      ''
        just --justfile ${../Justfile} --summary > "$out"
        grep -Fxq 'arch-workstation build check check-arch check-fast default' "$out"
        just --justfile ${../Justfile} --dry-run arch-workstation update >> "$out" 2>&1
        grep -Fq 'nix run .#arch-workstation -- --update' "$out"
      '';
}
