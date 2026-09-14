# nix-config

[![Checks](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Nix](https://img.shields.io/badge/Nix-flakes-5277C3)](https://nixos.org/)

Declarative configuration for one Arch workstation. Nix evaluates and builds the
configuration; Arch adapters converge native state; Home Manager owns the user
environment.

![Arch workstation preview](docs/assets/preview.png)

## Operators

```bash
just check-fast
just check
just build
just arch-workstation
just arch-workstation update
just arch-workstation verbose
just arch-workstation purge
```

AI preparation is explicit (`just prepare-ai`). Runner reconciliation and
registration are separate; tokens never enter Nix or Git. See the runbooks in
`docs/`.

## Configuration

`configuration.nix` imports the selected Host. Host defaults live under
`hosts/arch`; ordinary definitions override them. The public namespace is typed:

```nix
networking.hostname.name = "arch";
networking.hostname.enable = true;
networking.firewall.enable = true;
networking.hotspot.enable = false;
hardware.initramfs.enable = true;
services.gitlabRunner.instances.frontend.enable = true;
```

See [docs/configuration.md](docs/configuration.md) and [CONTEXT.md](CONTEXT.md).

## Developers

Keep one owner per package, account, file and service. Add isolated fixtures for
changed contracts, then run `just check-fast`, `just check`, `just build`, the
Home Manager activation build and `git diff --check`. Checks use temporary paths,
fake native commands and VMs; they never mutate the workstation.

`lib/` evaluates and composes, `hosts/` declares machine values,
`platforms/arch/` implements privileged adapters, `modules/` owns capabilities,
`profiles/` and `homes/` compose Home Manager, `checks/` validates contracts,
and `docs/` contains current operator procedures.
