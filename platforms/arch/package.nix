{
  lib,
  pkgs,
  deploymentUser,
  username,
  packages,
  hardware,
  capabilities ? import ../../lib/default-capabilities.nix,
  systemSettings ? null,
  aiConfig ? null,
  aiArtifacts ? null,
  moduleGroups ? [ ],
  moduleSystemUnits ? [ ],
}:
let
  ai =
    if aiConfig == null then
      null
    else
      import ./ai {
        inherit pkgs hardware;
        config = aiConfig;
        artifacts = aiArtifacts;
        tailscale = capabilities.tailscale;
      };
in
pkgs.writeShellApplication {
  name = "arch-switch";
  runtimeInputs = with pkgs; [
    coreutils
    diffutils
    findutils
    gawk
    gnugrep
    gnused
  ];
  text = ''
    readonly system_python=${pkgs.python3}/bin/python3
    readonly system_adapter=${
      lib.fileset.toSource {
        root = ./system;
        fileset = lib.fileset.unions [
          ./system/runtime.py
          ./system/files.py
          ./system/firewall.py
          ./system/hotspot.py
        ];
      }
    }/runtime.py
    readonly system_manifest=${
      if systemSettings == null then
        pkgs.writeText "unmanaged-system.json" "{}"
      else
        systemSettings.manifest
    }
    readonly ai_python=${pkgs.python3}/bin/python3
    readonly ai_adapter=${
      lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./ai/runtime.py
          ./system/files.py
        ];
      }
    }/ai/runtime.py
    readonly ai_manifest=${
      if ai == null then
        pkgs.writeText "unmanaged-ai.json" (builtins.toJSON { llama = false; })
      else
        ai.manifest
    }
    readonly fs_root=""
    readonly native_bin=/usr/bin
    readonly managed_identity=644:0:0
    readonly files=${./files}
    readonly curl_bin=${pkgs.curl}/bin/curl
    readonly tar_bin=${pkgs.libarchive}/bin/bsdtar
    readonly flock_bin=${pkgs.util-linux}/bin/flock
    readonly manage_network=${if capabilities.networking then "1" else "0"}
    readonly manage_tailscale=${if capabilities.tailscale then "1" else "0"}
    readonly manage_desktop=${if capabilities.desktop.enable then "1" else "0"}
    readonly manage_sunshine=${
      if capabilities.desktop.enable && capabilities.programs.sunshine.enable then "1" else "0"
    }
    readonly manage_initramfs=${if capabilities.initramfs then "1" else "0"}
    readonly expected_user=${lib.escapeShellArg username}
    pacman_packages=(${lib.escapeShellArgs packages.pacman})
    lizardbyte_package_names=(${lib.escapeShellArgs packages.lizardbyte})
    lizardbyte_packages=(${lib.escapeShellArgs (map (name: "lizardbyte/${name}") packages.lizardbyte)})
    aur_packages=(${lib.escapeShellArgs packages.aur})
    required_groups=(${
      lib.escapeShellArgs (
        lib.unique (deploymentUser.groups ++ moduleGroups ++ lib.optional deploymentUser.admin "wheel")
      )
    })
    system_units=(${
      lib.escapeShellArgs (
        lib.unique ((import ./services.nix { inherit lib capabilities; }) ++ moduleSystemUnits)
      )
    })
    initramfs_modules=(${lib.escapeShellArgs (lib.optionals capabilities.initramfs hardware.initramfsModules)})
    initramfs_images=(${lib.escapeShellArgs (lib.optionals capabilities.initramfs hardware.initramfsImages)})
    user_services=(${
      lib.escapeShellArgs (
        lib.optional hardware.openrazer "openrazer-daemon.service"
        ++ lib.optional (
          capabilities.desktop.enable && capabilities.programs.sunshine.enable
        ) "app-dev.lizardbyte.app.Sunshine.service"
      )
    })
  ''
  + builtins.readFile ./arch-switch.sh;
}
