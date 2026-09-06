# AGENTS Instructions

## Worktree and change workflow

- Work in the normal `~/.config/nix` checkout and preserve unrelated edits.
  Read [CONTEXT.md](CONTEXT.md) before changing composition or terminology.
- Implement behavior before documenting it. Stage exact intended paths before
  flake evaluation; never stage result links, registries or mutable host state.
- Use scoped Conventional Commit subjects: `type(scope): imperative subject`.
- Keep one owner for each package, file, account and service. Hide fixed policy
  behind small interfaces and keep test dependencies private.
- Name executable packaging `package.nix`, inventories `packages.nix`, and Python
  tests `tests/test_*.py`. Update imports, checks and docs when ownership moves.

## Source ownership

| Path | Owns | Constraint |
| --- | --- | --- |
| `flake.nix` | Explicit Host selection and output wiring | No directory discovery, implicit overlays or inline checks |
| `hosts/<name>/` | Identity, login users, hardware intent, selections and instance values | Provision login accounts outside deployment |
| `platforms/arch/` | Arch realization, native inventory and pacman repositories | Consume policy values without implementing Host or instance policy |
| `profiles/` | Reusable general-purpose bundles | Exclude hardware, Host names, secrets, service accounts and Runner instances |
| `homes/<user>/` | User differences and reviewed preferences | Keep shared behavior in its Module |
| `modules/home/` | Shared home behavior and graphical unit policy | Call Arch-owned desktop executables |
| `modules/gitlab-runner/` | Runner interfaces, derived identities, fixed security, native requirements, runtime and tests | Host supplies instance values; Platform and Profiles must not implement Runner policy |
| `checks/` and Module checks | Source validation | Use isolated fixtures, never the real machine |

Arch owns Nix, graphical/session executables, core OS packages, drivers, kernel
integration, PAM, polkit and system services. Home Manager owns portable CLI and
development packages, static files and safe user-unit policy. Graphical units
must call Arch-owned `/usr/bin` or `/usr/lib` paths; do not add desktop binaries
or GPU wrappers to the home profile. Keep `nix.conf` directly tracked, never
Home Manager-generated.

## Live-state boundary

Source builds are not authorization to deploy. Arch bootstrap/deployment, Home
Manager activation, package managers, service changes and Runner mutations
require a task that includes that live state. Inspect the exact target before
an authorized mutation. Runner status/check, Arch inventory queries and Noctalia
capture/deploy dry runs also inspect external state; do not use them as source
tests or retire repositories during validation.

Never read or print KeePassXC databases/INI files, systemd credentials, Runner
tokens/config, private keys or ignored secrets. Keep real authentication and
registration material out of expressions, derivations, arguments, logs, fixtures,
Git and the Nix store.

## Deployment invariants

- Routine `arch-switch` checks local packages and never installs or updates them.
  Missing packages exit 3. Only explicit `--update` permits full `pacman -Syu`
  followed by AUR convergence. Preserve the running-kernel/reboot gate.
- Compare content and metadata before writing. Record pending actions before
  writes and clear them only after success. Repair runtime drift on repeat runs.
  Lock mutations and preserve active lock inodes.
- Preserve unowned mkinitcpio settings. Derive hardware intent from the Host,
  never loaded-module detection; change only the managed module addition.
- Deployment profile names label the user's complete composition. Do not turn
  them into profile-selection switches.
- Do not add generic cleanup, automatic garbage collection, package removal,
  directory backup services or Runner purge.

## Desktop and home invariants

- Keep UWSM as the Hyprland entrypoint and one startup owner per application.
  Do not copy package-provided units or track generated `.wants/` links; target
  drop-ins at canonical package unit names.
- KeePassXC loads minimized and unlocks manually. Preserve the bounded tray-host
  readiness wait and degraded startup. Do not deliver credentials, probe unlocked
  collections or restart the vault to repair its tray icon.
- Noctalia starts independently of KeePassXC and uses a runtime file key.
  Keep initial storage preparation offline, preserve archived data and never
  regenerate a missing established key.
- Tray consumers follow Noctalia. Keep Vicinae's bounded, degraded tray wait and
  couple its lifetime to Noctalia so it releases the watcher before shell stops.
  Do not propagate shell restarts to Vesktop or KeePassXC. Do not restore
  Remmina applet autostart. Keep Vesktop compatibility flags app-specific.
- `modules/home/noctalia-config/` owns preference exchange and its tests;
  `homes/<user>/noctalia/config.toml` owns reviewed preferences. Home Manager
  alone deploys the config link. Do not copy GUI state wholesale into Git,
  silently discard overrides or bypass validation warnings. Report only safe
  diagnostic context; raw warnings can contain private settings.
- Override replacement requires stopped Noctalia, a private recovery receipt
  and preservation of unowned sections. Capture changes the repository snapshot,
  not live overrides; dry runs still inspect live settings.
- Link the locked Neovim input as one directory. Project Hyprland recursively
  into a writable non-VCS directory, with preflight before Home Manager links
  change. Reject worktrees and adjacent backups; do not migrate or delete them.
- Link each managed `~/.agents/skills/<name>` directory as a unit. Leaf-file
  projection and adjacent backups can break skill discovery.

## Runner invariants

Runner is optional. Each instance owns one account, home, subordinate range,
Podman socket, manager and registration. Reject overlapping ranges and
supplementary host roles. Service accounts receive no password, wheel membership,
Home Manager profile or desktop policy.

A manager can access only its instance's rootless Podman socket. Jobs receive
no host socket, stay unprivileged and use concurrency one. Keep these fixed,
not configurable. Required interfaces indicate readiness, never routing policy.
Removing a declaration does not authorize retiring its runtime state.

## Validation and documentation

Use focused checks during edits and the complete flake checks for composition
or orchestration changes:

```bash
nix build --no-link .#checks.x86_64-linux.source-format
nix flake check
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
nix build --no-link .#arch-switch .#runnerctl
git diff --check
```

Keep permanent tests for stable interfaces, security, repeat execution, failure
recovery and generated unit relationships. Use fake native commands and temporary
paths. Never point a source-validation harness at the real machine.
Keep `.github/workflows/check.yml` limited to source checks and builds, with
commit-pinned actions and read-only repository permissions. Workflow linting
belongs in `nix flake check`.

Keep each document focused: `README.md` is the user/developer entry point,
`docs/` owns operator procedures and recovery, `CONTEXT.md` defines composition,
and this file governs agent changes. Link to executable inventories instead of
copying them; omit historical migration narrative while retaining required
preparation and recovery instructions. `files/home/AGENTS.md` is the concise
home-root source; repository-specific rules stay here.
