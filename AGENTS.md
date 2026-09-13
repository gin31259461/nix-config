# AGENTS Instructions

## Scope and ownership

Read [CONTEXT.md](CONTEXT.md) before changing composition. The selected host
entry is `configuration.nix`; it imports `hosts/arch` and contains user
overrides. Host baselines use `lib.mkDefault`; ordinary module definitions win.
Unknown fields must fail evaluation and import order must not provide precedence.

Keep one owner for each package, file, account and service:

| Path | Responsibility |
| --- | --- |
| `flake.nix` | Output wiring and explicit composition |
| `configuration.nix`, `hosts/` | Host identity, hardware, defaults and instances |
| `lib/` | Schema evaluation, normalization and deployment composition |
| `platforms/arch/` | Arch packages, native services and privileged adapters |
| `modules/` | Capability interfaces and feature implementations |
| `profiles/`, `homes/` | Reusable and user-specific Home Manager composition |
| `checks/` | Isolated source and integration validation |
| `docs/` | Current operator procedures |

Arch owns system packages, `/etc`, system services, kernel, PAM, polkit and
native networking. Home Manager owns portable user packages, static home files
and safe user services. Service accounts do not receive human home composition.

## Deployment contracts

Core prerequisites fail fast. An optional adapter may return `not ready` only
when required preparation has never completed. Ownership conflicts, invalid
receipts, command failures and runtime drift are errors. Preserve command, exit
status, stdout and stderr from privileged native commands; `--verbose` must
reach Nix and both adapters.

Routine deployment never installs packages. Only explicit `--update` runs full
pacman/AUR convergence. Preserve the running-kernel gate, mutation lock,
pending markers and idempotent repeat behavior. Disabling a capability withdraws
management but does not remove packages, files, services, registrations or
application data.

AI preparation is explicit. The selector, build receipt and every declared
model must match the declaration before service convergence. llama-swap,
llama-server and Caddy stay loopback-only; unrelated Tailscale Serve state is
not overwritten.

GitLab Runner remains outside workstation deployment. Each enabled instance owns
one service account, subordinate ID ranges, rootless Podman runtime, manager and
registration. Keep jobs unprivileged, sockets isolated and security policy fixed.
Registration tokens must not enter Git, Nix derivations or unredacted logs.

## Data and session safety

Never read or print KeePassXC databases, credentials, private keys, Runner
tokens or secret payloads. Mutable Noctalia data stays outside source. Home
activation must not clean application data. Keep UWSM as the Hyprland entry
point and one startup owner per application. Do not copy package units or
generated `.wants/` links. Keep project source trees outside managed runtime
paths.

## Python and module design

Nix is the source of truth for the Python interpreter, dependencies and tools.
Keep project-level Ruff settings in `pyproject.toml`; do not introduce uv or a
second lockfile unless the ownership decision changes. Prefer normal package
imports and explicit dependency injection. A shared module needs two real
adapters or callers; preserve owner-specific filesystem and token contracts.
Keep runtime source filesets separate from tests where packaging permits.

Tests should cross the public interface, use temporary paths, fake native
commands or isolated VMs, and assert stable capability contracts. Do not bind
AI tests to a specific model identity or incidental metadata. Test schema
validation, declaration propagation, preparation/drift handling, loopback
policy, conflicts, idempotence and disabled-state preservation.

## Validation and editing

Use `apply_patch` for edits. Preserve unrelated dirty worktree changes and do
not use destructive Git recovery commands without explicit authorization.
Never run live deployment, registration, package installation or cleanup to
validate source or documentation.

For ordinary changes run focused checks. For composition, adapter or deployment
changes complete:

```bash
just check-fast
just check
just build
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

Build only optional outputs that are exported by the current configuration.
Update README for public workflows, `docs/` for operator behavior, and
`CONTEXT.md` when composition or ownership changes. Keep this file limited to
agent decisions and current guardrails; remove superseded plans.
