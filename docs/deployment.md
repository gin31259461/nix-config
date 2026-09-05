# Deployment behavior and recovery

`arch-workstation` builds its Home Manager activation package, runs
`arch-switch`, then runs `home-switch`. If Arch fails, home activation does not
start. If home activation fails, the completed Arch work remains; fix the reported
path or configuration and rerun the deployment.

## What each mode does

| Mode | Inventory | System changes |
| --- | --- | --- |
| `arch-switch --check` | Remote Arch/LizardByte/AUR resolution | None |
| `arch-switch` | Installed packages only | Converge files and runtime policy |
| `arch-switch --update` | Remote resolution and installed packages | Full pacman upgrade, AUR convergence, then policy |

All modes check the expected login identity and administrator membership.
The deployment wrapper accepts `--update` as its first argument and forwards
remaining arguments to Home Manager. Backup-extension arguments are rejected.

The root of native package ownership is
[packages.nix](../platforms/arch/packages.nix). Host hardware and optional Module
requirements contribute to that inventory. Removing an entry does not uninstall
it.

## Convergence and interrupted work

Managed file replacements compare contents, mode and owner. A changed file is
installed through a temporary file in the destination directory and renamed
into place. The controller refuses managed-file symlinks.

NetworkManager restart, systemd reload and initramfs generation use pending
markers under `/var/lib/nix-config/arch/`. Markers are written before related
configuration changes and removed after successful actions. Leave them in place
when diagnosing a failure; rerunning the deployment completes pending work.

The controller preserves existing mkinitcpio settings and owns only its marked
`MODULES+=` addition. The Host declares required early modules and expected
initramfs image paths. Missing images trigger regeneration. Files and hooks
outside this ownership are not a complete initramfs input-tracking system;
changes made externally may still require the native rebuild workflow.

Managed container-network modules are loaded when absent, before managed sysctl
keys are compared with runtime values on every deployment. The modules-load
destination retains its existing name, `nix-config-podman.conf`.
Required system services are enabled or started only when needed. A private
login-runtime lock serializes Arch deployments; an overlapping invocation
returns 75. This lock does not coordinate unrelated manual administrative tools.

## Respond to failures

| Result | Next action |
| --- | --- |
| Exit 2: invalid or incompatible arguments | Use `--help`; choose one mode |
| Exit 3: missing declared packages | Rerun the deployment with `--update` |
| Exit 75: running kernel modules unavailable | Reboot into the installed kernel, then rerun |
| Exit 75: another deployment running | Let that invocation finish, then retry |
| Unmanaged LizardByte repository detected | Reconcile ownership of the exact pacman entry before retrying |
| Managed target is a symlink | Inspect the target and establish ownership; deployment will not replace it |
| Command or initramfs generation failure | Correct the reported prerequisite and rerun; pending work remains recorded |
| Home projection or file collision | Resolve the exact worktree/backup/conflicting file, then retry without backup flags |

Updating the kernel intentionally stops before AUR and subsequent policy
convergence if its running module directory disappeared. After reboot, rerun
the same update command.

Home preflight rejects `.git` at the Neovim/Hyprland targets or their ancestors
along both logical and resolved paths, and adjacent `.bak`, `.backup` and `~` paths. It does not delete
anything. Keep development repositories elsewhere and avoid adding backup
extensions to runtime configuration.

Routine convergence requires neither GitLab connectivity nor a Runner
registration. Nix downloads can still be needed to build a new deployment;
remote inventory checks and updates require their own network connectivity.
