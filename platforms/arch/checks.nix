{ pkgs, ... }:
{
  system-firewall-integration = import ./system/tests/firewall-vm.nix { inherit pkgs; };
  system-settings-interface =
    assert import ./system/tests/interface.nix {
      inherit pkgs;
      inherit (pkgs) lib;
    };
    pkgs.writeText "system-settings-interface" "passed";
  system-settings-tests =
    pkgs.runCommand "system-settings-tests" { nativeBuildInputs = [ pkgs.python3 ]; }
      ''
        python ${./system}/tests/test_system.py
        touch "$out"
      '';
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
