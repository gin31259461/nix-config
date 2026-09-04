{
  lib,
  packageInventory,
}:
let
  requiredPackages = [
    "aardvark-dns"
    "ca-certificates"
    "ca-certificates-utils"
    "coreutils"
    "curl"
    "fuse-overlayfs"
    "iproute2"
    "netavark"
    "p11-kit"
    "passt"
    "podman"
    "slirp4netns"
    "shadow"
    "systemd"
    "util-linux"
  ];
  missingPackages = lib.subtractLists packageInventory requiredPackages;
in
assert lib.assertMsg (missingPackages == [ ])
  "Arch GitLab Runner packages are missing from the native inventory: ${builtins.concatStringsSep ", " missingPackages}";
{
  inherit requiredPackages;
  platform = import ./arch-platform.nix;
}
