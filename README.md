# nix-config

[![Checks](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Nix](https://img.shields.io/badge/Nix-flakes-5277C3)](https://nixos.org/)

Declarative configuration for one x86_64 Arch Linux workstation. Nix builds the
deployment, Arch adapters apply native package and system policy, and Home
Manager manages the user environment. This is an existing-machine configuration,
not a NixOS system or an Arch installer.

![Arch workstation preview](docs/assets/preview.png)

## Versions and Environment

This repository pins reproducible upstream channels, external inputs, and AI model artifacts:

| Component | Target / Release | Pinned Source / Revision |
| --- | --- | --- |
| **Platform** | Arch Linux (`x86_64-linux`) | Host user `abnertu`, kernel module match |
| **Nixpkgs** | `nixos-26.05` | [`c3eea5b`](https://github.com/NixOS/nixpkgs/tree/c3eea5b2156db11c7eeeada3dc737711255b253e) |
| **Home Manager** | `release-26.05` (`stateVersion = "26.05"`) | [`ec17201`](https://github.com/nix-community/home-manager/tree/ec172013fa62135f58fb58dd17ae9651e8f39727) |
| **Personal Agent** | Standalone Assistant & SearXNG | [`7cdfc49`](https://github.com/gin31259461/personal-agent/tree/7cdfc49851c70be14ba0e4d80bc77e65446a153a) |
| **OrbitVim** | Pinned Neovim Runtime Config | [`335ad2e`](https://github.com/Orbit-Lua/orbitvim/tree/335ad2e5c83eaa7e7a2d0688efd012855c41e379) |
| **Hyprland Config** | Pinned Hyprland & Waybar Config | [`09402e2`](https://github.com/Orbit-Lua/hypr/tree/09402e2cf53f62683ac0726b770e22c3c7fedd96) |
| **llama.cpp** | Local ROCm0/Vulkan Inference Engine | [`434ddbb`](https://github.com/ggml-org/llama.cpp/tree/434ddbbc0e30522e897670681e503b797c12b7c1) |
| **Default AI Model** | Qwen3.6-35B-A3B-GGUF (MXFP4_MOE) | [`a483e9e`](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) |
| **DevShell Tooling** | Isolated Dev Toolchain | Python 3 (`tomli-w`), Pyright, Ruff, Just, Nixfmt |

## Operators

Run commands from this checkout. Source checks and builds require Nix with
`nix-command` and `flakes` enabled. This checkout provides [nix.conf](nix.conf) to
enable these features and configure build concurrency (`max-jobs = auto`, `cores = 0`)
as well as substitute download concurrency (`max-substitution-jobs = 64`,
`http-connections = 50`). Use `just` to list the available recipes; if
it is not installed yet, `nix run .#just -- <recipe>` runs the same recipes.

Start by reviewing [configuration.nix](configuration.nix) and the selected
[Host defaults](hosts/arch/default.nix), then validate and build without activation:

```bash
just check-fast
just check
just build
```

Deployment must run on Arch as the selected login user, currently `abnertu`.
The account must already exist, belong to `wheel`, and have native Nix, `yay`
and the required native commands available. The running kernel must have a
matching module directory. Review the [deployment prerequisites and recovery
procedure](docs/deployment.md), including hotspot preparation and Noctalia's
first storage activation, before applying the configuration.

| Command | Effect on the workstation |
| --- | --- |
| `just arch-workstation` | Apply Arch state and the built home generation. |
| `just arch-workstation update` | Upgrade pacman/AUR packages, then deploy. |
| `just arch-workstation verbose` | Deploy with full diagnostics. |
| `just arch-workstation purge` | Remove managed Arch state; skip the home. |

Routine deployment does not install packages. Missing declared packages stop the
run with exit code 3. `update` performs a full pacman upgrade followed by declared
AUR package convergence. A kernel upgrade may require a reboot before convergence
can continue. Arch changes remain applied if the later Home Manager activation
fails. Use `just arch-workstation update verbose` to include complete Nix and
adapter diagnostics during an update.

Disabling an Arch capability withdraws future management; it does not remove
existing state. Explicit `purge` preserves installed packages, accounts, Runner
registrations and mutable application data. See the
[deployment runbook](docs/deployment.md) for cleanup scope and failure handling.

AI assets require explicit preparation with `just prepare-ai`. An enabled AI
module that has never completed preparation may be skipped; invalid receipts,
conflicts and runtime failures stop deployment. Runner reconciliation,
registration and verification use separate commands in the
[Runner runbook](docs/runners.md). Keep tokens outside Git, Nix and logs.

The pinned Personal Agent package is converged as an optional native service when
its external runtime configuration is ready. See the
[Personal Agent runbook](docs/personal-agent.md); Discord and Notion identifiers,
tokens and SQLite state remain outside Git and the Nix store.

## Configuration

Edit [configuration.nix](configuration.nix) to override the selected Host.
Host baselines use `lib.mkDefault`; ordinary definitions override them without
depending on import order. For example:

```nix
{ ... }:
{
  imports = [ ./hosts/arch ];

  networking.hotspot.enable = false;
  virtualisation.kvm.gui.enable = false;
  users.users.abnertu.home.programs.git.settings.init.defaultBranch = "main";
}
```

The [public schema](lib/configuration-options.nix) and feature interfaces reject
unknown options, wrong types and invalid combinations. Inspect a resolved value
without deployment:

```bash
nix eval .#lib.configurations.arch.networking.hostname.name
```

User overrides belong under `users.users.<name>.home`; reusable Home Manager
behavior belongs in profiles or home modules. Keep Home Manager `stateVersion`
unchanged during routine updates. See the [configuration guide](docs/configuration.md)
for capability switches and disable semantics.

## Documentation

| Guide | Use it for |
| --- | --- |
| [Configuration](docs/configuration.md) | Public options, overrides and resolved values. |
| [Deployment](docs/deployment.md) | Prerequisites, execution order, diagnostics and recovery. |
| [System settings](docs/system-settings.md) | Native ownership, preflight and pending actions. |
| [Wi-Fi hotspot](docs/hotspot.md) | Preparing and adopting a NetworkManager AP connection. |
| [Desktop session](docs/desktop-session.md) | UWSM startup, tray ownership and Noctalia storage. |
| [Noctalia configuration](docs/noctalia-config.md) | Capturing, deploying and recovering reviewed UI preferences. |
| [AI service](docs/ai.md) | Preparing llama.cpp and models, then deploying loopback services. |
| [GitLab Runners](docs/runners.md) | Preparing, registering and verifying isolated Runner instances. |
| [Personal Agent](docs/personal-agent.md) | Runtime configuration, pinned package updates and service operations. |

## Developers

Read [AGENTS.md](./AGENTS.md) for editing constraints and [CONTEXT.md](./CONTEXT.md)
for the composition model. Keep one owner per package, account, file and service:

| Path | Responsibility |
| --- | --- |
| `lib/` | Typed evaluation, normalization and deployment composition. |
| `hosts/` | Host identity, users, hardware and capability defaults. |
| `platforms/arch/` | Native packages, adapters and system services. |
| `modules/` | Capability interfaces and their implementations. |
| `profiles/`, `homes/` | Reusable and user-specific Home Manager composition. |
| `checks/` | Shared checks and isolated fixtures. |

Feature tests also live beside their owning modules and adapters. Use
`nix develop` for the Python, Pyright, Ruff and Just development environment. For
composition or adapter changes, run:

```bash
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

`check-fast` validates formatting, all Python types with Pyright's standard mode,
and selected interfaces; `check` builds all flake checks, including the home,
adapter tests and firewall VM test. Tests use
temporary paths and fake native commands or isolated VMs. These commands build
and validate source without activating the workstation.
