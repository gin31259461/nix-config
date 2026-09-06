# Arch workstation

[![Check](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Home Manager](https://img.shields.io/badge/Home_Manager-26.05-5277C3)](https://github.com/nix-community/home-manager/tree/release-26.05)

Personal Arch Linux configuration combining a UWSM-managed Hyprland desktop,
Noctalia, Home Manager development tools, and optional rootless GitLab Runners.
The declared target is `arch-workstation` on `x86_64-linux`, with home
configuration `abnertu@arch`.

![Preview](docs/assets/preview.png)

## Build, then deploy

Use the checkout at `~/.config/nix` on an existing Arch installation with flakes
enabled. The tracked [nix.conf](nix.conf) supplies Nix's user configuration.
Provision the declared login user, `wheel` access, the Arch-owned Nix daemon,
`yay`, and the [native prerequisites](platforms/arch/arch-switch.sh) first.
This repository does not create login accounts or install the base OS.

```bash
nix flake check
nix build --no-link .#arch-workstation

# First deployment or newly declared native packages:
nix run .#arch-workstation -- --update

# Routine deployment:
nix run .#arch-workstation
```

Run as the selected login user; the controller uses sudo for system changes.
For first-time Noctalia storage setup, follow the
[offline preparation steps](docs/desktop-session.md#prepare-storage-on-a-new-home)
before activation.

Deployment builds the home, converges Arch, then activates Home Manager.
Routine runs check installed packages and repair managed files/runtime policy;
missing packages exit 3. Only `--update` performs a full `pacman -Syu` followed
by AUR convergence. A kernel mismatch exits 75: reboot and rerun the update.
Arch packages are not locked by `flake.lock`, and home activation failure does
not roll back completed Arch changes.

Once `just` is installed, use these shortcuts. Before then, use
`nix run .#just -- <recipe>`.

| Command | Action |
| --- | --- |
| `just check-fast` | Formatting, Python static checks and declaration interfaces |
| `just check` | All flake checks, including the home build |
| `just build` | Build the deployment without activation |
| `just arch-workstation` | Deploy using installed native packages |
| `just arch-workstation update` | Fully update native packages and deploy |
| `just check-arch` | Resolve external package inventories without deployment |

## Configure your workstation

Arch owns desktop executables, drivers and system services. Home Manager owns
platform-independent CLI packages, static home files and user-unit policy.
Graphical units invoke Arch-owned paths.

| Responsibility | Source |
| --- | --- |
| Host identity and deployment selection | [hosts/arch/default.nix](hosts/arch/default.nix) |
| Login users, profiles and modules | [hosts/arch/users.nix](hosts/arch/users.nix) |
| Hardware intent | [hosts/arch/hardware.nix](hosts/arch/hardware.nix) |
| Native packages | [platforms/arch/packages.nix](platforms/arch/packages.nix) |
| Reusable CLI/development bundles | [profiles/default.nix](profiles/default.nix) |
| User preferences | [homes/abnertu/home.nix](homes/abnertu/home.nix) |
| AI and virtualization selection | [hosts/arch/default.nix](hosts/arch/default.nix), [operator preparation](docs/deployment.md#ai-and-virtualization) |
| Shared home behavior | [modules/home/default.nix](modules/home/default.nix) |
| Runner instances | [hosts/arch/gitlab-runners.nix](hosts/arch/gitlab-runners.nix) |

The deployment name labels the user's entire selected composition; it does not
switch to an isolated profile. [CONTEXT.md](CONTEXT.md) defines the composition
model and ownership vocabulary.

### Noctalia preferences

```bash
nix run .#noctalia-config -- capture --dry-run
nix run .#noctalia-config -- capture
```

Capture writes reviewed-scope preferences to
[homes/abnertu/noctalia/config.toml](homes/abnertu/noctalia/config.toml).
It validates before writing and leaves GUI overrides untouched. Inspect the
result locally before committing. For applying the snapshot, resolving warnings
and replacing conflicting GUI overrides, see [preference exchange](docs/noctalia-config.md).

### Locked Neovim and Hyprland inputs

Develop these configurations in separate repositories outside runtime paths.
Test a local Hyprland checkout without changing the lock:

```bash
nix build --no-link --override-input hypr-config path:$HOME/codebase/hypr \
  '.#homeConfigurations."abnertu@arch".activationPackage'

# Adopt a published revision:
nix flake update hypr-config
nix flake check
```

Use `neovim-config` for Neovim. Neovim and each managed skill are linked as
whole directories; Hyprland uses recursive links inside a writable directory.
Activation rejects worktrees and adjacent backups at managed runtime targets.

## Operations and development

- [Deployment and recovery](docs/deployment.md): prerequisites, update modes,
  exit codes, locks and interrupted actions.
- [Desktop session](docs/desktop-session.md): tray startup, Vesktop compatibility,
  KeePassXC and Noctalia storage recovery.
- [Noctalia preferences](docs/noctalia-config.md): capture, validation, deployment
  and override receipts.
- [Runner operations](docs/runners.md): explicit instance setup, registration
  and verification. Workstation deployment does not run these operations.
- [AGENTS.md](./AGENTS.md): coding-agent rules and validation boundaries.

Stage exact intended inputs before flake evaluation. Use `nix fmt -- path/to/file.nix`
for Nix formatting, then `nix flake check` and `git diff --check`.
[CI](.github/workflows/check.yml) runs source checks and builds on Ubuntu without
activating the workstation. Native-command tests use fake commands and temporary
paths. No deployment performs automatic package removal, garbage collection,
directory backups or Runner retirement.
