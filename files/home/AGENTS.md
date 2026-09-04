# AGENTS Instructions

## Configuration ownership

The active machine configuration repository is `~/.config/nix`. Read its
`AGENTS.md` before changing workstation configuration, Home Manager modules,
Arch system policy, graphical session services, or GitLab Runner instances.

Hyprland and Neovim are non-flake inputs of that repository. Make upstream
changes in their own repositories; update the corresponding lock entry only
when intentionally adopting a new revision.

## Worktree rules

- Use the normal Git worktree at `~/.config/nix`; do not use the retired `dot`
  alias or treat `$HOME` as a Git worktree.
- Keep credentials, tokens, application databases, generated state, caches,
  and private keys outside configuration repositories and the Nix store.
- Do not run activation, package managers, service changes, Runner
  registration, or destructive retirement steps merely to validate source.
- The configuration intentionally has no directory backup service, generic
  cleanup, automatic garbage collection, or Runner purge command.

Other repositories under `$HOME` own their own instructions and worktrees.
