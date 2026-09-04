# AGENTS Instructions

## Scope and sources of truth

This repository is the declarative source of truth for the owner's Arch and
future NixOS machines. Read `CONTEXT.md` before changing composition vocabulary.
Read `docs/migrations/from-dotfiles-homebase.md` while Runner adoption or legacy
repository retirement remains incomplete.

Use these ownership boundaries:

- `hosts/<name>/` owns machine identity, login users, profile/module selection,
  hardware, and host-specific values.
- `platforms/` owns generic Arch or NixOS realization and native package
  ownership. It must not know host identity or application instances.
- `profiles/` owns reusable general-purpose bundles. Keep hostnames, hardware,
  secrets, service accounts, and GitLab Runner instances out of profiles.
- `homes/<user>/` owns personal Home Manager differences; shared behavior
  belongs in `modules/home/`.
- A module owns its interface, implementation, service accounts, and internal
  platform adapters. GitLab Runner policy belongs only in
  `modules/gitlab-runner/` and host instance configuration.
- `flake.nix` is the explicit composition entrypoint. Do not add directory
  auto-discovery or implicit overlay loading.

Give every package, file, account, and service exactly one owner. Prefer a deep
module that derives names and fixed security behavior over options that leak
implementation details to callers.

## Platform and runtime policy

- Arch owns Nix, graphical/session executables, core OS packages, kernel and
  driver integration, PAM, polkit, and system services. Keep its third-party
  pacman repositories and package inventory in the Arch adapter.
- On Arch, do not add graphical executables, GPU bridges, or driver wrappers to
  Home Manager. User units must call the Arch-owned stable system path.
- Home Manager owns platform-independent CLI/development packages, static home
  configuration, and user-unit policy whose activation is safe.
- NixOS owns system accounts, services, hardware, and system packages through
  NixOS modules.
- Login users belong in `hosts/<name>/users.nix`. A service account belongs to
  its module and receives no Home Manager profile, password, wheel membership,
  desktop policy, or unrelated host role.

Routine `arch-switch` runs do not update or install packages. A missing declared
package must stop deployment and require an explicit `--update`; that path uses
a complete `pacman -Syu` before converging AUR packages. Do not introduce a
partial-upgrade path or make routine activation update the system implicitly.

## Graphical session invariants

- Keep UWSM as the Hyprland entrypoint and give every application one startup
  owner.
- Treat the Arch package inventory and `/usr/bin` or `/usr/lib` paths as
  authoritative for graphical-session executables. Home Manager may own only
  unit policy and application configuration.
- Do not copy package-provided units or track generated `.wants/` symlinks.
- Preserve KeePassXC, Secret Service, Noctalia, tray-consumer, and tray-repair
  ordering. Keep credentials and mutable security state outside the Nix store.

Manage the locked Neovim input as one directory link. Project Hyprland
recursively into a clean, writable, non-VCS directory. Never project either
input into an existing Git worktree, where VCS metadata or migration backups
could enter runtime discovery.

## GitLab Runner invariants

- Keep Runner optional, never a profile or platform concern. Configure
  instances under their host.
- Preserve one account, home, subordinate-ID range, Podman socket, manager, and
  registration per instance; reject overlapping subordinate ranges.
- A manager may access only its instance's rootless Podman socket. Job
  containers receive no host socket, stay unprivileged, and use concurrency one.
- Treat `network.requiredInterface` as readiness only, not routing policy.
- Keep registration tokens and persisted metadata out of Nix expressions,
  derivations, command arguments, logs, fixtures, and the Nix store.

## Repository and safety rules

- Work in the normal `~/.config/nix` worktree. `nix.conf` is tracked directly;
  Home Manager must not generate it.
- Link each `~/.agents/skills/<name>` directory as a unit. Leaf-file projection
  and migration backups can prevent Codex skill discovery.
- `files/home/AGENTS.md` is the concise source for the Home Manager-managed
  instruction file at the home root; detailed ownership stays here.
- Preserve unrelated dirty files and stage exact paths only. Flakes see only
  tracked files, so add intended inputs before evaluating them.
- Use scoped Conventional Commit subjects: `type(scope): imperative subject`.
- Never commit result links, local registries, secrets, credentials, tokens,
  private keys, application databases, or mutable host state.

Builds, evaluation, formatting, shell linting, and fake harnesses are safe.
Never run Arch bootstrap/apply, Home Manager or NixOS switch, package managers,
service enablement, Runner registration, or repository retirement merely to
validate source. Inspect the exact target before any authorized live operation.
Do not read or print KeePassXC databases/INI files, systemd credentials, Runner
tokens/config, private keys, or ignored secrets.

The project intentionally provides no generic cleanup, automatic garbage
collection, directory backup service, or Runner purge command.

## Validation and documentation

Use the narrowest safe check that covers the changed interface:

```bash
nix flake check
nix build '.#homeConfigurations."abnertu@arch".activationPackage'
nix build .#arch-switch .#runnerctl
```

For a NixOS host, build its affected system closure. Run Runner `status` or
`verify` only when external host state or connectivity is explicitly in scope.
Keep permanent tests for stable interfaces, security invariants, and
non-trivial orchestration; remove migration-only comparisons when their old
owner is retired.

`README.md` owns current operator workflows, `CONTEXT.md` owns vocabulary,
`AGENTS.md` owns coding-agent decisions, and migration documents own temporary
transition steps. Update source first, then only documents whose public
contract or ownership changed. Do not retain completed migration instructions
as a parallel architecture.
