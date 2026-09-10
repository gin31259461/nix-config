# nix-config

[![Check](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Home Manager](https://img.shields.io/badge/Home_Manager-26.05-5277C3)](https://github.com/nix-community/home-manager/tree/release-26.05)

Declarative Arch Linux workstation configuration built with Nix and Home Manager.
Arch adapters own native packages, system files, services, kernel integration and
host runtime policy. Home Manager owns portable user packages, files and user
services. `configuration.nix` is the single configuration entry point.

![Desktop preview](docs/assets/preview.png)

## Configure

Keep the Host import and override only the values you need:

```nix
{ ... }:
{
  imports = [ ./hosts/arch ];

  networking.firewall.enable = false;
  services.fstrim.enable = false;
  virtualisation.kvm.gui.enable = false;
}
```

Host defaults use `lib.mkDefault`; ordinary definitions in `configuration.nix`
win. Unknown options and invalid values fail evaluation. See
[configuration](docs/configuration.md) and [composition](CONTEXT.md).

## Validate

```bash
just check-fast
just check
just build
```

`just check` runs the complete flake checks with Nix traces and build logs. Source
checks use isolated fixtures and do not mutate the workstation.

## Prepare optional modules

Optional modules that require external or local initialization are prepared
explicitly. An enabled optional deployment module that has never been prepared is
skipped with a highlighted warning; a configured module with invalid or drifting
state still fails.

```bash
# Build pinned llama.cpp and install the selected model.
just prepare-ai
just prepare-ai build
just prepare-ai model

# GitLab Runner lifecycle.
just prepare-runner frontend
GITLAB_RUNNER_TOKEN=glrt-... just initialize-runner frontend
just verify-runner frontend
just status-runner frontend
```

Runner operations remain separate from workstation deployment. See
[AI operations](docs/ai.md) and [Runner operations](docs/runners.md).

## Deploy

```bash
# Routine convergence.
just arch-workstation

# Install/upgrade missing Arch and AUR packages, then converge.
just arch-workstation update

# Full Nix and adapter diagnostics.
just arch-workstation verbose
just arch-workstation update verbose
```

Deployment always uses `--show-trace --print-build-logs` for Nix operations.
`verbose` additionally enables Nix `--verbose`, prints each privileged adapter
native command and preserves its complete stdout/stderr. Native command failures
also include both streams without verbose mode.

For a direct Nix invocation, app arguments cannot retroactively change Nix's own
evaluation logging. Use both sides explicitly when full diagnostics are needed:

```bash
nix run --show-trace --print-build-logs --verbose .#arch-workstation -- --verbose
```

Routine deployment does not install missing packages; it exits 3 and tells the
operator to rerun with `update`. A running-kernel mismatch exits 75 and requires a
reboot. Pending actions are retained across failures and retried on the next run.
See [deployment](docs/deployment.md).

## Repository layout

| Path | Responsibility |
| --- | --- |
| `configuration.nix` | Selected Host entry and local overrides |
| `hosts/` | Machine defaults, identity, hardware and instances |
| `lib/` | Typed configuration evaluation and deployment composition |
| `platforms/arch/` | Arch packages, services and privileged adapters |
| `modules/` | Feature-owned interfaces and implementations |
| `profiles/` | Reusable Home Manager bundles |
| `homes/` | User-specific Home Manager values |
| `checks/` | Source and integration checks |
| `docs/` | Current operator procedures |

Developer constraints are in [AGENTS.md](AGENTS.md). The current ownership and
composition vocabulary is defined in [CONTEXT.md](CONTEXT.md).
