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

The wrapper accepts `--update` first and forwards remaining arguments to Home
Manager. Adjacent-backup arguments are rejected. A deployment profile labels
the complete user composition, not a subset of selected profiles.

## Understand the boundary between stages

The deployment artifact includes the built Home Manager activation package.
At runtime, Arch convergence must succeed before Home Manager activation begins.
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
