# AGENTS Instructions

## Work from declared ownership

Read [CONTEXT.md](CONTEXT.md) before changing composition. `configuration.nix` is
the selected Host entry. Public options belong in their owning typed interface;
Host baselines use `lib.mkDefault`, while user overrides use ordinary module
definitions. Do not use import order as precedence or accept unknown fields.

Keep one owner per package, file, account and service:

| Path | Owner |
| --- | --- |
| `flake.nix` | Output wiring and explicit composition |
| `configuration.nix`, `hosts/` | Host selection, identity, hardware and instance values |
| `lib/` | Schema evaluation, normalization and deployment composition |
| `platforms/arch/` | Arch-native packages, services and privileged adapters |
| `modules/` | Capability interfaces and feature-owned implementations |
| `profiles/`, `homes/` | Reusable and user-specific Home Manager composition |
| `checks/` | Isolated source validation |
| `docs/` | Current operator procedures only |

Arch owns system packages, `/etc`, system services, kernel integration, PAM,
polkit and native networking. Home Manager owns portable user packages, static
home files and safe user services. Service accounts never receive a human home
composition.

## Preserve deployment contracts

Core deployment prerequisites fail fast. Optional modules may be skipped only
when an explicit adapter readiness result proves that required preparation has
not completed. Never convert ownership conflicts, invalid state, command
failures or runtime drift into optional skips.

All privileged Python native commands use the shared Arch native adapter.
Failures must preserve command, exit status, stdout and stderr. `--verbose` must
reach both Nix orchestration and privileged adapters. Do not introduce a new
subprocess wrapper that silently captures or discards diagnostics. Sensitive
values must be specifically redacted rather than suppressing an entire command's
output.

Routine deployment never installs packages. Only explicit `--update` permits the
full pacman update and AUR convergence. Preserve the running-kernel gate, pending
action markers, mutation lock and idempotent repeat behavior. A disabled
capability withdraws management but does not retire existing packages, files,
services, registrations or application data.

AI preparation remains explicit. The prepared llama.cpp selector, build receipt
and model must match the declaration before service convergence. Caddy and
llama-server remain loopback-only; unrelated Tailscale Serve configuration is
not overwritten.

GitLab Runner remains outside workstation deployment. Each enabled instance owns
one service account, subordinate ID ranges, rootless Podman runtime, manager and
registration. Preserve unprivileged jobs, isolated sockets and fixed security
policy. Registration tokens must not enter Git, Nix derivations or unredacted
logs.

## Preserve user data

Never read or print KeePassXC databases, credentials, private keys, Runner tokens
or secret payloads. Noctalia storage keys and mutable application data stay
outside source. Home activation must not become application-data cleanup.

Keep UWSM as the Hyprland entry point and one startup owner per application. Do
not copy package units or generated `.wants/` links. Keep project source trees
outside managed runtime paths.

## Validate changes

Use focused checks during implementation and complete checks for composition,
adapter or deployment changes:

```bash
just check-fast
just check
just build
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

Tests use temporary paths, fake native commands and isolated VMs. Source checks
must never mutate the real workstation. Build optional outputs only when their
configuration exports them.

Keep documentation limited to current behavior. Delete superseded planning,
research and migration documents instead of maintaining historical narratives.
README is the entry point, `docs/` contains operator runbooks, CONTEXT defines
composition, and this file contains repository change constraints.
