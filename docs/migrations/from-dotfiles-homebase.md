# Migration from bare dotfiles and Homebase

This guide exists only while the legacy bare dotfiles, Homebase, and
platform-infra repositories still own live workstation behavior.

## Target

The normal Git worktree at `~/.config/nix` becomes the only configuration
source. Home Manager owns the user environment, NixOS modules own NixOS system
state, and tested Arch adapters own the remaining native Arch state.

GitLab Runner becomes an optional module with NixOS and Arch adapters. The
platform-infra repository can be retired only after every real Runner target is
an Arch or NixOS host represented here.

## Excluded behavior

Do not migrate the old directory backup unit, timer, configuration, or helper.
Do not migrate Homebase cleanup catalogs or scripts, and do not replace them
with automatic garbage collection or purge commands.

## Sequence

1. Establish a buildable flake and the `abnertu@arch` Home Manager output.
2. Install Nix through the Arch-native bootstrap path.
3. Migrate login users, profiles, package ownership, and static home files.
4. Preserve graphical-session ownership and credential ordering.
5. Add read-only checks and idempotent apply behavior for native Arch state.
6. Evaluate shared NixOS modules without inventing a deployable host.
7. Port GitLab Runner invariants and adopt existing registrations without
   reading them during Nix evaluation or placing secrets in the store.
8. Build and inspect every activation before switching the live host.
9. Disable the legacy backup timer and stop using Homebase only after the new
   owners pass their checks. Do not reproduce the timer in this repository.
10. Archive legacy repositories after a stable operating period, then remove
    local checkouts in a separately reviewed destructive step.

## Cutover checks

- Every managed file, package, account, and unit has one owner.
- Mutable state and credentials remain machine-local.
- Home Manager does not manage `~/.config/nix/nix.conf` because the repository
  tracks that file directly.
- Hyprland and Neovim use locked non-flake inputs instead of Git submodules.
- GitLab Runner instances preserve their accounts, homes, subordinate ranges,
  manager isolation, and existing registration metadata.
- Migration-only differential tests are removed after the legacy owner is
  retired.

## Current gate

Source migration, native Nix evaluation, and deployment builds are complete.
Nix is installed and its daemon is healthy. The Arch package plane, LizardByte
repository, updated kernel, and Home Manager generation are active. The
Home Manager-owned user units pass systemd verification and the live user
session has no failed units. Runner adoption remains pending. Until the Runner
checks succeed, do not remove the bare Git directory, Homebase source, or
`platform-infra` checkout.
