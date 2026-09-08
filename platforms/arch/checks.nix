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
        python ${./system}/tests/test_hotspot.py
        touch "$out"
      '';
  ai-services-tests = pkgs.runCommand "ai-services-tests" { nativeBuildInputs = [ pkgs.python3 ]; } ''
    python ${./ai/tests/test_ai.py} ${
      pkgs.lib.fileset.toSource {
        root = ./.;
        fileset = pkgs.lib.fileset.unions [
          ./ai/runtime.py
          ./system/files.py
        ];
      }
    }/ai/runtime.py
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
