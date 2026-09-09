# nix-config

[![Check](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Home Manager](https://img.shields.io/badge/Home_Manager-26.05-5277C3)](https://github.com/nix-community/home-manager/tree/release-26.05)

An Arch workstation declared through a NixOS-style
[configuration.nix](configuration.nix): typed namespaces, explicit imports,
overridable defaults and capability switches. Arch supplies the operating system
and desktop executables; Home Manager supplies portable tools, static files and
user units. The selected composition is `arch-workstation` / `abnertu@arch` on
`x86_64-linux`, with a UWSM Hyprland desktop and optional rootless GitLab Runners.

![Desktop preview](docs/assets/preview.png)

## Configure

Keep the Host import in `configuration.nix` and add your changes there:

```nix
{ ... }:
{
  imports = [ ./hosts/arch ];
  networking.firewall.enable = false;
  services.fstrim.enable = false;
  virtualisation.kvm.gui.enable = false;
  programs.vicinae.enable = false;
}
```

Public capability switches default to true. Host values use `mkDefault`, so
ordinary definitions override them. Required identity and fixed security policy
remain constrained. [Configuration guidance](docs/configuration.md) explains
namespaces, Home Manager overrides, list merging and what disabling means.
The [schema](lib/configuration-options.nix) and executable
[inventories](platforms/arch/packages.nix) are the source of truth.

This is an Arch configuration, not a NixOS installation. New default-on settings
include time synchronization, journal, console, logind and TRIM policy; review
[adoption prerequisites](docs/system-settings.md) before deploying. The selected
Wi-Fi hotspot adopts a prepared NetworkManager connection; see
[hotspot preparation](docs/hotspot.md) for local credential setup and recovery.
The native Ollama/Vulkan capability and optional tailnet proxy require explicit
[AI service preparation](docs/ai.md), including review of the Ollama GPU ID and
existing Tailscale Serve routes.

## Build and use

Work in `~/.config/nix` on an existing Arch installation with flakes enabled.
Provision the declared login account, `wheel` access, Arch-owned Nix daemon,
`yay` and the controller's [native prerequisites](platforms/arch/arch-switch.sh).
Keep [nix.conf](nix.conf) directly tracked. Builds do not activate configuration:

```bash
nix eval .#configurations.arch.networking.hostName
nix build --no-link .#arch-workstation
```

After reviewing [deployment preparation](docs/deployment.md), explicitly apply:

```bash
# First deployment or newly selected native packages: full Arch/AUR update.
nix run .#arch-workstation -- --update

# Routine convergence; missing packages exit 3 without installing them.
nix run .#arch-workstation
```

The deployment applies Arch policy, then the exact built Home Manager generation.
It never registers Runners or removes packages automatically. A kernel mismatch
requires reboot and retry. See [deployment recovery](docs/deployment.md),
[desktop/storage preparation](docs/desktop-session.md),
[Noctalia preference exchange](docs/noctalia-config.md) and
[Runner operations](docs/runners.md) for live workflows. Ollama, Caddy and Serve
checks and recovery are documented in [AI service operations](docs/ai.md).

`just arch-workstation` accepts composable `update` and `verbose` options; for
example, `just arch-workstation update verbose` performs a full system update
and enables verbose Home Manager activation output. The options may be supplied
in either order. These are shortcuts;
`nix run .#just -- <recipe>` works before Home Manager activation.
`arch-switch`, `home-switch`, and enabled `noctalia-config` / `runnerctl` outputs
also provide their separate interfaces. Inspect live state only deliberately;
`arch-switch --check` is an external inventory query, not a source test.

## Develop and validate

Preserve unrelated work and stage exact intended paths before flake evaluation;
Git flakes omit untracked files. Do not stage result links or mutable state.

```bash
nix build --no-link .#checks.x86_64-linux.source-format
nix flake check
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
nix build --no-link .#arch-switch .#runnerctl
git diff --check
```

Checks use isolated fixtures, fake native commands and a firewall VM. They never
attach to the real desktop or change host services. `runnerctl` exists only when
an instance is selected. `configurations` is a custom inspection output and
produces an informational unknown-output warning during flake checking.

[CONTEXT.md](CONTEXT.md) defines the composition and ownership model;
[AGENTS.md](AGENTS.md) governs agent changes. The
[implementation plan](docs/configuration-plan.md) and
[official-source research](docs/nixos-module-research.md) record the design and
validation contract for the configuration interface.
