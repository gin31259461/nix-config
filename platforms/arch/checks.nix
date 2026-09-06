{ pkgs, ... }:
{
  arch-switch-tests =
    pkgs.runCommand "arch-switch-tests"
      {
        nativeBuildInputs = with pkgs; [
          python3
          bash
          coreutils
          diffutils
          findutils
          gawk
          gnugrep
          gnused
          util-linux
        ];
      }
      ''
        python ${./tests}/test_arch_switch.py ${./.}/arch-switch.sh
        touch "$out"
      '';
}
