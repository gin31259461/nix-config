# nix-config

[![Checks](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Nix flakes](https://img.shields.io/badge/Nix-flakes-5277C3)](https://nixos.org/)

Nix-built configuration for one existing `x86_64-linux` Arch workstation. Nix evaluates typed settings and produces static home and native policy; small Arch adapters reconcile live system state. Home Manager activates the user environment after Arch convergence. This repository is neither a NixOS configuration nor an Arch installer.

![Arch workstation preview](docs/assets/preview.png)

## First build

Use this checkout on Arch Linux with Nix flakes and `just` available. The selected human account must already exist before activation. If this is a fresh Arch installation without Nix or Just, follow the [bootstrap procedure](docs/deployment.md#bootstrap).

Review [configuration.nix](configuration.nix) and [Host defaults](hosts/arch/default.nix), then run from the repository root:

```bash
just check-fast
just check
just build
```

These commands validate and build source without changing the running workstation. A successful `just build` produces the fixed deployment artifact; it does not activate it. For the exact prerequisites, effects and recovery path before first activation, read [deployment](docs/deployment.md).

```bash
just arch-workstation          # Converge installed Arch state, then activate the built home.
just arch-workstation update   # Also upgrade/converge declared pacman and AUR packages.
just arch-workstation verbose  # Include Nix, Home Manager and adapter diagnostics.
just arch-workstation purge    # Remove managed Arch deployment state; skip home activation.
```

Routine deployment does not install packages. Missing declared native packages stop it with exit code 3; `update` is the explicit package operation. Arch changes and Home Manager activation do not share a rollback transaction. A selected hotspot with absent declared hardware is a core preflight error. Enabled optional AI or Personal Agent may be skipped only when required preparation has never completed; invalid receipts, ownership conflicts and runtime drift fail the run.

## Configure

[configuration.nix](configuration.nix) imports the selected Host. Baselines in `hosts/` use `lib.mkDefault`; ordinary option definitions in `configuration.nix` override them. Unknown fields, invalid types and invalid combinations fail evaluation. Inspect a resolved value without activation:

```bash
nix eval .#lib.configurations.arch.networking.hostname.name
```

The [configuration guide](docs/configuration.md) explains public options and user overrides. Home Manager owns static home files and user services, often as managed links into a Nix generation. The Arch adapter installs or merges Nix-generated native files and checks live ownership, permissions and service state. Secrets, mutable application data, prepared GGUF models and compiled llama.cpp binaries stay outside Git and the Nix store. This boundary is explained in [CONTEXT.md](CONTEXT.md).

External Hyprland and Neovim source trees remain outside Home Manager-managed runtime paths. Their pinned revisions are adopted through intentional flake lock updates. The current source and package inventories belong to the owning Nix modules and `flake.lock`, not this page.

## Operator guides

| Guide | When to read it |
| --- | --- |
| [Deployment](docs/deployment.md) | Bootstrap, activation, updates, purge and recovery |
| [Configuration](docs/configuration.md) | Options, precedence and resolved values |
| [System settings](docs/system-settings.md) | Native ownership, preflight and pending markers |
| [Hotspot](docs/hotspot.md) | Adopt an existing NetworkManager AP |
| [Desktop session](docs/desktop-session.md) | UWSM, startup ownership and Noctalia storage |
| [Noctalia configuration](docs/noctalia-config.md) | Capture and deploy reviewed UI preferences |
| [AI service](docs/ai.md) | Prepare external assets and converge loopback services |
| [GitLab Runners](docs/runners.md) | Separate reconcile, registration and verification lifecycle |
| [Personal Agent](docs/personal-agent.md) | External runtime configuration and native service |

`just --list` shows the available recipes. AI preparation (`just prepare-ai`) and Runner operations are separate from routine workstation deployment; their guides describe live prerequisites and side effects.

## Development

Read [AGENTS.md](AGENTS.md) before changing the repository and [CONTEXT.md](CONTEXT.md) for the composition model. `lib/` owns typed evaluation and deployment composition; `hosts/` owns host defaults; `platforms/arch/` owns native adapters; `modules/` owns capabilities; `profiles/` and `homes/` own Home Manager composition. Feature tests live near their owners.

For composition or adapter changes, run the source-only gate:

```bash
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

Checks use temporary roots, fake commands and isolated VMs. They do not deploy or inspect protected live data.
