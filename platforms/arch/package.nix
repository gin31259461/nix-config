{
  lib,
  pkgs,
  deploymentUser,
  username,
  packages,
  hardware,
  systemSettings ? null,
  moduleGroups ? [ ],
  moduleSystemUnits ? [ ],
}:
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
        ];
      }
    }/runtime.py
    readonly system_manifest=${
      if systemSettings == null then
        pkgs.writeText "unmanaged-system.json" "{}"
      else
        systemSettings.manifest
    }
    readonly fs_root=""
    readonly native_bin=/usr/bin
    readonly managed_identity=644:0:0
    readonly files=${./files}
    readonly curl_bin=${pkgs.curl}/bin/curl
    readonly tar_bin=${pkgs.libarchive}/bin/bsdtar
    readonly flock_bin=${pkgs.util-linux}/bin/flock
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
    system_units=(${lib.escapeShellArgs (lib.unique ((import ./services.nix) ++ moduleSystemUnits))})
    initramfs_modules=(${lib.escapeShellArgs hardware.initramfsModules})
    initramfs_images=(${lib.escapeShellArgs hardware.initramfsImages})
    user_services=(${
      lib.escapeShellArgs (
        lib.optional hardware.openrazer "openrazer-daemon.service"
        ++ [ "app-dev.lizardbyte.app.Sunshine.service" ]
      )
    })
  ''
  + builtins.readFile ./arch-switch.sh;
}
