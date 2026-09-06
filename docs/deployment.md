# Workstation deployment

Run `arch-workstation` as the Host's selected login user on Arch Linux.
The account must already exist with administrator membership, native Nix and
`yay`, and the prerequisites checked by
[arch-switch.sh](../platforms/arch/arch-switch.sh). Sudo performs system changes.
Boot a kernel whose module directory exists before deployment.

## Choose an operation

| Command | Behavior |
| --- | --- |
| `nix build --no-link .#arch-workstation` | Build artifacts without activation |
| `nix run .#arch-switch -- --check` | Resolve Arch, LizardByte and AUR inventories without system convergence |
| `nix run .#arch-workstation` | Check installed packages, converge Arch, activate the home |
| `nix run .#arch-workstation -- --update` | Resolve inventories, fully upgrade pacman packages, converge AUR and deploy |

Inventory checks inspect external state and need connectivity. Routine package
checks are local, though Nix may still download build dependencies. Native
packages are not version-locked by the flake. Removing an inventory entry does
not uninstall the package.

Both deployment modes maintain the managed LizardByte pacman include; only
`--update` installs or upgrades packages. Its signature exception is confined
to that repository. Existing unmanaged repository declarations require explicit
ownership reconciliation.

The wrapper accepts `--update` first and optional `--verbose`. Other arguments
are rejected before Arch convergence, including source/target overrides and
adjacent-backup arguments. `home-switch` alone accepts `--verbose` and
`--dry-run`; a home dry run does not preview Arch changes. A deployment profile
labels the complete user composition, not a subset of selected profiles.

## Understand the boundary between stages

The deployment artifact includes the built Home Manager activation package.
At runtime, Arch convergence must succeed before Home Manager activation begins.
`home-switch` activates that exact package with Home Manager driver version 0;
its activation script manages the generation profile at the write boundary,
after preflight. It does not re-evaluate the checkout. Source and target changes
require building a new deployment artifact.
A home failure leaves completed Arch work in place: fix the reported problem
and rerun. These stages do not share a rollback transaction.

First-time Noctalia storage preparation requires its service stopped; follow
[desktop preparation](desktop-session.md#prepare-storage-on-a-new-home).
Group membership changes require a new login session.

## Repeat execution and interrupted work

File updates compare contents, owner and mode, then replace through a temporary
file in the destination directory. Managed-file symlinks are rejected. Healthy,
unchanged system services are not restarted merely because deployment repeats.
Runtime module and sysctl drift is repaired even when files already match.

Network restart, systemd reload and initramfs work use pending markers under
`/var/lib/nix-config/arch/`. Each marker precedes its related write and is cleared
only after successful action. Preserve markers on failure; rerunning completes
unfinished work. A private login-runtime lock serializes Arch mutations;
unrelated manual administrative commands do not participate in that lock.

The Host supplies early-module intent and expected initramfs images. Deployment
preserves unowned mkinitcpio settings and manages only its marked `MODULES+=`
addition. Missing images trigger regeneration. Changes to external hooks or
other unowned inputs may still require the native initramfs rebuild workflow.

## Resolve a failed run

| Symptom | Next step |
| --- | --- |
| Exit 2 | Check arguments with `--help`; choose one mode |
| Exit 3, missing native packages | Run the deployment with `--update` |
| Exit 75, running kernel modules unavailable | Reboot into the installed kernel and rerun |
| Exit 75, another deployment running | Wait for that invocation, then retry |
| Unmanaged LizardByte repository | Reconcile the exact pacman declaration before retrying |
| Managed file is a symlink | Inspect ownership; do not replace it blindly |
| Initramfs or native-command failure | Fix the prerequisite and rerun with pending markers intact |
| Home projection collision | Resolve the exact worktree, backup or conflicting file |

After a pacman upgrade, a missing running-kernel module directory stops the
workflow before AUR convergence and subsequent policy changes. Reboot and repeat
the same update command.

Neovim/Hyprland preflight rejects `.git` at managed targets or their ancestors
along logical and resolved paths, plus adjacent `.bak`, `.backup` and `~` paths.
It runs before Home Manager link changes and does not remove collisions. Keep
input development repositories outside runtime paths.

Workstation deployment does not require GitLab registration or perform Runner
reconciliation. Use the separate [Runner workflow](runners.md) when that state
is in scope. There is no automatic package removal, garbage collection,
directory backup service or Runner purge.

## AI and virtualization

The Host selects both capabilities in [hosts/arch/default.nix](../hosts/arch/default.nix).
Each parent defaults to disabled when omitted. Codex, skills presets, KVM and
Podman child switches default to enabled and take effect only when their parent
is enabled. The optional KVM GUI defaults to disabled.

- `ai.enable` gates `ai.codex.enable` (the AUR Codex package) and
  `ai.skillsPresets.enable` (the repository's existing skill presets).
  Home Manager links each skill directory as a unit for every declared login
  user's composition. Disabling presets removes their managed links on home
  activation, without deleting the source presets.
- `virtualization.enable` gates `virtualization.kvm.enable` and
  `virtualization.podman.enable`. The Module's
  [inventory](../modules/virtualization/packages.nix) owns native dependencies.
  KVM adds the deployment login user to the `kvm` group. Log out and back in
  after the first deployment changes group membership.

KVM uses QEMU directly, with user networking and optional UEFI firmware.
Enable CPU virtualization in firmware before use. The kernel loads its
CPU-specific KVM driver automatically; no CPU vendor detection or initramfs
rewrite is needed by this Module. For an existing VM disk, a typical invocation
is `/usr/bin/qemu-system-x86_64 -accel kvm -cpu host -m 4G -drive file=vm.qcow2,format=qcow2 -nic user`.
Disk creation, guest installation and bridge networking remain operator choices.

Set `virtualization.kvm.gui.enable = true;` to add virt-manager, libvirt and
the DNS/DHCP and nftables tools used by libvirt virtual networks.
The current Host enables it explicitly. Both `virtualization.enable` and
`virtualization.kvm.enable` must also be true. Arch deployment enables and starts
the package-provided local `libvirtd.socket`; repeat deployment repairs socket
drift without restarting running guests. It uses libvirt's standard polkit
authentication and does not grant passwordless management or enable TCP access.

After `just arch-workstation update`, launch
`/usr/bin/virt-manager --connect qemu:///system` from your graphical session and
authenticate if prompted. Use its wizard to create a VM. Virtual networks and
their autostart remain explicit choices in virt-manager; deployment does not
create guests, pools or networks. Store system-managed VM disks in a
libvirt-accessible storage pool rather than assuming your private home is
accessible. Existing custom or modular libvirt daemon setups must be reconciled
before deployment; deployment does not migrate or unmask their units.

Turning the GUI off stops declaring its packages and socket. It does not stop
libvirt or delete existing guests. See libvirt's
[socket activation](https://libvirt.org/daemons.html) and
[authentication](https://libvirt.org/auth.html) documentation.

Podman runs through the Arch-owned executable without an automatically enabled
API socket. Before rootless use, provision non-overlapping subordinate UID and
GID ranges for the login account in `/etc/subuid` and `/etc/subgid`, as part of
login-account preparation. Keep those ranges separate from Runner instances.
The Module does not modify existing container storage or Runner registrations.
See the [Arch Podman manual](https://man.archlinux.org/man/podman.1.en) and
[QEMU guidance](https://wiki.archlinux.org/title/QEMU) for runtime preparation.

Use the normal explicit update workflow to install newly selected packages.
Routine deployment still exits 3 if any declared package is missing. Disabling
a capability stops declaring its requirements; it does not remove installed
packages, revoke groups or retire runtime state.

## Source validation ownership

[Deployment packaging and tests](../lib/deployment/) own the ordered workflow
and the exact-generation activation contract. [Arch checks](../platforms/arch/checks.nix)
exercise native convergence with fake commands. Global [checks](../checks/default.nix)
wire cross-stage ordering, workflow linting and source validation.

Login homes must use distinct absolute paths under `/home/`, with each path
segment containing letters, digits, `_` or `-`. Nested paths such as
`/home/team/user` are supported; empty segments, traversal and control characters
are rejected during Host evaluation.
