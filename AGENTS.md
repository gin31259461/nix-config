# AGENTS Instructions

## Before editing

Read `CONTEXT.md` when changing composition or terminology. Use the normal
`~/.config/nix` worktree, preserve unrelated changes, and stage exact intended
paths before flake evaluation. Do not commit result links, registries or mutable
host state. Use scoped Conventional Commit subjects: `type(scope): imperative subject`.

## Put changes with their owner

- `flake.nix` explicitly selects Hosts and connects outputs. Keep checks in
  `checks/` or the owning Module. Do not add directory auto-discovery or implicit
  overlay loading.
- `hosts/<name>/` owns identity, login users, hardware intent, selections and
  instance values. Login accounts are provisioned outside deployment.
- `platforms/arch/` owns Arch realization, native package inventory and pacman
  repositories. Pass policy values to it; do not teach it Host identity or
  application instances.
- `profiles/` owns reusable general-purpose bundles. Exclude hardware, Host
  names, secrets, service accounts and Runner instances.
- `homes/<user>/` owns user differences; `modules/home/` owns shared home
  behavior and graphical unit policy.
- `modules/gitlab-runner/` owns Runner interfaces, derived identities, fixed
  security policy, native requirements, runtime code and tests. Host declarations
  own instance values; Profiles and Platform must not implement Runner policy.
- Give each package, file, account and service one owner. Prefer a small
  interface that hides fixed behavior. Keep test dependencies private.
- Use names that identify responsibility: `package.nix` for executable
  packaging, `packages.nix` for inventories, `tests/test_*.py` for Python tests.
  Update imports, checks and documentation when moving an owner.

## Preserve deployment contracts

- Arch owns Nix, graphical/session executables, core OS packages, drivers,
  kernel integration, PAM, polkit and system services. Home Manager owns
  platform-independent CLI/development packages, static files and safe
  user-unit policy. Graphical units call Arch-owned `/usr/bin` or `/usr/lib`
  paths; never add graphical executables or GPU wrappers to the home profile.
- Routine `arch-switch` uses local package checks and never installs or updates
  packages. Missing packages exit 3. Only explicit `--update` may run a complete
  `pacman -Syu`, followed by AUR convergence. Preserve the kernel/reboot gate.
- Compare content and metadata before writing. Record pending actions before
  writes, clear them only after success, and repair runtime drift on repeat
  invocation. Keep locking around mutations; do not remove active lock inodes.
- Preserve unowned mkinitcpio settings. Hardware intent comes from the Host,
  not loaded-module detection. Change only the managed module addition.
- Deployment profile names label the user's complete composition; do not
  silently turn them into profile-selection switches.
- Do not implement generic cleanup, automatic garbage collection, package
  removal, directory backup services or Runner purge.

## Protect home and Runner state

- Keep UWSM as the Hyprland entrypoint and one startup owner per application.
  KeePassXC loads minimized at login but unlocks manually: no credential
  delivery, unlocked collection probe or tray-repair restart. Noctalia uses a
  runtime file key and starts independently of KeePassXC; tray consumers follow
  Noctalia. Keep its one-time storage transition offline, preserve archived
  data, and never regenerate a missing established key. Vicinae's tray timeout permits
  degraded startup. Do not restore Remmina applet autostart.
- Never copy package-provided units or track generated `.wants/` links.
  Target drop-ins at the package's canonical unit name.
- `modules/home/noctalia-config/` owns capture/deploy behavior and its tests;
  `homes/<user>/noctalia/config.toml` owns reviewed preferences. Home Manager
  alone deploys the config link. Do not copy GUI state wholesale into Git or
  silently clear overrides. Override replacement requires a stopped Noctalia,
  a private recovery receipt, and preservation of unowned sections. Dry-run
  capture/deploy still inspect live settings and are not source-validation tests.
- Link the locked Neovim input as one directory; recursively project Hyprland
  into a clean writable non-VCS directory. Keep projection preflight before
  Home Manager link changes. Reject worktrees and adjacent backups instead of
  deleting or migrating them automatically.
- Link each managed `~/.agents/skills/<name>` directory as a unit. Leaf-file
  projection and adjacent backups can break skill discovery.
- Keep `nix.conf` tracked directly; Home Manager must not generate it.
- Runner remains optional. Each instance owns one account, home, subordinate
  range, Podman socket, manager and registration. Reject overlapping ranges
  and supplementary host roles. A service account gets no password, wheel
  membership, Home Manager profile or desktop policy.
- A manager can access only its instance's rootless Podman socket. Jobs get
  no host socket, remain unprivileged and use concurrency one. Do not expose
  these invariants as options. Required network interfaces indicate readiness,
  never enforced routing.
- Keep real tokens and registration metadata out of expressions, derivations,
  arguments, logs, fixtures and the Nix store. Do not read or print KeePassXC
  databases/INI files, systemd credentials, Runner tokens/config, private keys
  or ignored secrets.

## Validate source without deploying

Safe checks:

```bash
nix build --no-link .#checks.x86_64-linux.source-format
nix flake check
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
nix build --no-link .#arch-switch .#runnerctl
git diff --check
```

Use focused checks while editing, then the complete flake checks for composition
or orchestration changes. Keep `.github/workflows/check.yml` limited to source
validation and builds, pin actions to commit hashes, and use read-only repository
permissions. Workflow linting is part of `nix flake check`.
Keep permanent tests for stable interfaces, security,
repeat execution, failure recovery and generated unit relationships. Use fake
native commands and temporary paths; never execute a source-validation harness
against the real machine.

Arch deployment/bootstrap, Home Manager switch, package managers, service
enablement and Runner reconcile/register/verify are live operations, not
validation. Runner status/check and Arch inventory queries also inspect
external state. Run them only when that state is explicitly in scope; inspect
the exact target before an authorized live mutation. Do not retire repositories
as a validation step.

## Keep documentation useful

Write implementation first. `README.md` is the human/developer entry point,
`docs/` explains operator recovery and Runner workflows, `CONTEXT.md` defines
composition, and this file governs AI changes. Update only the documents whose
contract changed; avoid duplicated inventories or historical migration prose.

`files/home/AGENTS.md` is the concise source for the home-root instructions.
Keep repository-specific details here rather than copying them to every project
under the home directory.
