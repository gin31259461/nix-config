# AGENTS Instructions

## Change the declared source

- Work in the normal `~/.config/nix` checkout; preserve unrelated edits. Read
  [CONTEXT.md](CONTEXT.md) before changing composition or terminology.
- Use `configuration.nix` as the explicit selected Host entry point. Declare
  typed, grouped options in their owning interface; use `mkDefault` for Host
  baselines and ordinary definitions for user overrides. Do not use import order
  as override precedence or silently accept unknown fields.
- Default public capability enable options to true. Gate every owned contribution
  with its effective parent/child selection. Keep required identity and fixed
  security policy constrained; never add switches that weaken Runner isolation.
- Implement behavior before documenting it. Stage exact intended paths before
  flake evaluation; exclude result links, registries, mutable state and secrets.
- Use scoped Conventional Commits: `type(scope): imperative subject`.
  Name executable packaging `package.nix`, inventories `packages.nix`, Python
  tests `tests/test_*.py`; update imports, checks and docs when ownership moves.

## Respect module and platform ownership

| Owner | Responsibility and boundary |
| --- | --- |
| `flake.nix` | Explicit Host selection and output wiring; no directory discovery, implicit overlays or inline checks |
| `configuration.nix`, `hosts/<name>/` | Entry overrides; Host defaults, identity, human users, hardware intent and instance values |
| `lib/configuration-options.nix`, `lib/eval-configuration.nix` | Typed composition and normalization into private adapter values; no native convergence |
| `platforms/arch/` | Arch realization, native inventories and pacman repositories; consume declared policy |
| `profiles/` | Reusable home bundles; no Host names, hardware policy, secrets, service accounts or Runner instances |
| `homes/<user>/` | Reviewed user differences; shared behavior stays in its Module |
| `modules/home/` | Shared home behavior and graphical unit policy using Arch-owned executables |
| `modules/gitlab-runner/` | Runner interface, derived identities, fixed security, native requirements, runtime and private tests |
| `checks/`, Module checks | Source validation with isolated fixtures, never the real machine |

Keep one owner per package, file, account and service. Hide fixed policy behind
small interfaces and keep test dependencies private. Arch owns Nix, graphical
and session binaries, core OS packages, drivers, kernel integration, PAM, polkit
and system services. Home Manager owns portable CLI/development packages, static
files and safe user-unit policy. Graphical units call `/usr/bin` or `/usr/lib`;
do not add desktop binaries or GPU wrappers to the home profile. Keep `nix.conf`
directly tracked, never Home Manager-generated. Provision human accounts before
deployment; service accounts never receive a home composition.

## Keep live state outside source validation

Source builds do not authorize deployment. Bootstrap, Arch/Home Manager
activation, package managers, service changes and Runner mutations require a
task that includes that live state. Inspect the exact target before an authorized
mutation. Runner status/check, Arch inventory queries and Noctalia capture/deploy
dry runs also inspect external state; never use them as source tests or retire
repositories during validation.

Never read or print KeePassXC databases/INI files, systemd credentials, Runner
tokens/config, private keys or ignored secrets. Keep authentication and
registration material out of expressions, derivations, arguments, logs,
fixtures, Git and the Nix store.

## Preserve convergence and recovery

- Routine `arch-switch` only checks installed packages; missing packages exit 3.
  Only explicit `--update` permits full `pacman -Syu` then AUR convergence.
  Preserve the running-kernel/reboot gate.
- False withdraws Arch declarations without retiring existing files, packages,
  services, registrations or pending actions. Home Manager retains its normal
  managed-generation transition semantics; never add application-data cleanup.
- AI false selections leave Ollama/Caddy files, services, models and Tailscale
  Serve routes untouched. Select Vulkan devices from Ollama's own numeric IDs;
  do not infer its ordinal from generic Vulkan inventory order. Keep Ollama and
  Caddy loopback-only, preserve Caddy sites during adoption, and never reset
  unrelated Serve configuration.
- Compare content and metadata before writes. Persist pending actions before
  mutation and clear only after success. Repair runtime drift on repeat runs.
  Lock mutations and preserve active lock inodes.
- Preserve unowned mkinitcpio settings; manage only the marked module addition.
  Derive hardware intent from the Host, never loaded-module detection. Disabled
  initramfs management leaves the existing addition and receipt untouched.
- Deployment profile names label the complete user composition, never a
  profile-selection mode. Do not add generic cleanup, automatic garbage
  collection, package removal, directory backup services or Runner purge.

## Preserve desktop relationships and private data

- Keep UWSM as Hyprland's entry point and one startup owner per application.
  Do not copy package units or track generated `.wants/` links; use drop-ins at
  canonical package unit names.
- KeePassXC starts minimized and unlocks manually. Preserve its bounded tray-host
  wait and degraded startup. Do not deliver credentials, probe unlocked
  collections or restart the vault to repair an icon.
- Noctalia starts independently of KeePassXC and uses a runtime file key.
  Prepare storage offline, preserve archives and never regenerate a missing
  established key.
- Tray consumers follow Noctalia. Keep Vicinae's bounded degraded wait and coupled
  lifetime so it releases the watcher before shell shutdown. Do not propagate
  shell restarts to Vesktop/KeePassXC or restore Remmina applet autostart. Keep
  Vesktop compatibility flags app-specific. Disabled consumers leave no Wants
  edge from Noctalia to their absent units.
- `modules/home/noctalia-config/` owns preference exchange and tests;
  `homes/<user>/noctalia/config.toml` owns reviewed preferences. Home Manager alone
  deploys the config link. Never copy GUI state wholesale, silently discard
  overrides or bypass validation warnings. Report safe diagnostic context only;
  raw warnings may contain private settings.
- Override replacement requires stopped Noctalia, a private recovery receipt and
  preservation of unowned sections. Capture edits the repository snapshot, not
  live overrides; dry runs still inspect live settings.
- Link the locked Neovim input as one directory. Project Hyprland recursively
  into a writable non-VCS directory with preflight before home links change.
  Reject worktrees and adjacent backups; never migrate or delete them.
- Link each managed `~/.agents/skills/<name>` directory as a unit. Leaf-file
  projection and adjacent backups can break discovery.

## Preserve Runner isolation

Runner remains optional even with default-on selection: zero enabled instances
exports no controller or native requirements. Each instance owns one account,
home, subordinate range, Podman socket, manager and registration. Reject
range overlap and supplementary Host roles. Service accounts have no password,
wheel membership, Home Manager profile or desktop policy.

A manager accesses only its own rootless Podman socket. Jobs receive no host
socket, stay unprivileged and use concurrency one. These are fixed policy.
Required interfaces indicate readiness, not routing. Removing or disabling an
instance never authorizes runtime retirement. Login-user virtualization toggles
must not suppress independent Runner requirements.

## Validate contracts and maintain focused documents

Use focused checks while editing; run the complete checks for composition or
orchestration changes:

```bash
nix build --no-link .#checks.x86_64-linux.source-format
nix flake check
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
nix build --no-link .#arch-switch .#runnerctl
git diff --check
```

Build optional outputs only when selected. Test stable interfaces, override
priorities, parent/child disabling, security, repeat execution, failure recovery
and generated unit relationships with temporary paths and fake native commands.
Keep workflow linting in flake checks. `.github/workflows/check.yml` contains only
source checks/builds, commit-pinned actions and read-only repository permissions.

Keep README as the user/developer entry point, `docs/` as operator procedures and
recovery, CONTEXT as composition terminology, and this file as agent constraints.
Link executable inventories instead of copying them. Omit retired migration
narrative while preserving preparation and recovery. `files/home/AGENTS.md`
remains the concise home-root source; repository-specific rules stay here.
