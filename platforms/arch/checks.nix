{ pkgs, llama-prepare, ... }:
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
        python ${./system}/tests/test_native.py ${./system}/native.py
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
  llama-prepare-interface =
    pkgs.runCommand "llama-prepare-interface"
      {
        nativeBuildInputs = [
          pkgs.python3
          pkgs.util-linux
        ];
      }
      ''
        ${llama-prepare}/bin/llama-prepare --help | grep -Fxq \
          'usage: llama-prepare [--build-only | --model-only]'
        if ${llama-prepare}/bin/llama-prepare --model-only >out 2>err; then exit 1; fi
        grep -Fq 'run llama-prepare as root' err
        grep -Fq '#define MAX_REPETITION_THRESHOLD 2000' ${../../modules/ai/prepare.sh}
        grep -Fq -- '-DVulkan_INCLUDE_DIR=/usr/include -DVulkan_LIBRARY=/usr/lib/libvulkan.so' \
          ${../../modules/ai/prepare.sh}
        grep -Fq '/run/lock/nix-config-llama-prepare.lock' ${../../modules/ai/prepare.sh}
        python ${../../modules/ai/tests/test_prepare.py} ${../../modules/ai/prepare.sh}
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
        python ${./tests}/test_optional_lifecycle.py ${./.}/arch-switch.sh
        touch "$out"
      '';
}
