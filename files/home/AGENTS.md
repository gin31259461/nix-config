# AGENTS Instructions

Workstation configuration is managed from `~/.config/nix`. Read that
repository's `AGENTS.md` before changing Arch policy, Home Manager configuration,
graphical startup or GitLab Runner instances.

- Use the normal configuration worktree. Do not treat the home directory as a
  Git worktree or use the retired `dot` alias.
- Develop Hyprland and Neovim inputs in their own repositories, outside runtime
  configuration paths. Adopt upstream changes through an intentional lock update.
- Keep credentials, tokens, private keys, application databases and generated
  state outside configuration repositories and the Nix store.
- Validate source with builds and isolated tests. Activation, package managers,
  service changes and Runner operations require a task that includes live state.
- Do not introduce automatic cleanup, directory backups, garbage collection or
  Runner purge into workstation deployment.

Other projects under the home directory own their own instructions and worktrees.
