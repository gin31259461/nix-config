# Arch workstation

[![Platform: Arch Linux](https://img.shields.io/badge/platform-Arch_Linux-1793D1?logo=archlinux)](https://archlinux.org/)
[![Check](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)
[![Home Manager](https://img.shields.io/badge/Home_Manager-26.05-5277C3)](https://github.com/nix-community/home-manager/tree/release-26.05)

Build and deploy an Arch workstation with native desktop applications, Home
Manager CLI tools and configuration, a UWSM-managed Hyprland session, and optional
rootless GitLab Runner instances.

The supported target is `arch-workstation` on `x86_64-linux`. It deploys host
`arch` and Home Manager configuration `abnertu@arch`. Host and user selections
are explicit in [flake.nix](flake.nix) and [hosts/arch](hosts/arch/default.nix).

## Start with a build

Use an existing Arch installation with Nix flakes enabled. This repository's
tracked `nix.conf` supplies the user configuration when the checkout is at
`~/.config/nix`; Home Manager does not generate that file.

From the checkout:

```bash
nix flake check
nix build --no-link .#arch-workstation
```

These commands evaluate configuration and build artifacts. They do not activate
Home Manager, change packages or services, or contact configured GitLab servers.
Nix may download locked inputs and build dependencies.

Before deployment, provision the declared login user with `wheel` access, the
Arch-owned Nix daemon, `yay`, and the native prerequisites checked by
[arch-switch.sh](platforms/arch/arch-switch.sh). Boot a kernel whose module
directory is installed. The project does not bootstrap login accounts.

## Deploy and update

Run deployments as the selected login user, not root. The controller uses sudo
for system changes.

```bash
# First deployment, or after adding native packages:
nix run .#arch-workstation -- --update

# Subsequent deployments:
nix run .#arch-workstation
```

The target builds its Home Manager activation package first, converges Arch, and
activates the home only after Arch succeeds. These stages are not one atomic
transaction: if home activation fails, completed Arch changes remain.

Routine deployment checks locally installed packages without querying remote
repositories. Missing packages stop it with exit code 3. It updates changed
configuration, repairs managed runtime settings, and starts required inactive
services. An already-converged run does not rebuild initramfs or restart healthy
services.

Only `--update` resolves remote inventories, installs the managed LizardByte
repository include, performs a complete `pacman -Syu`, and then converges AUR
packages. The signature exception is confined to the LizardByte repository.
Native packages are not version-locked by `flake.lock`.

If an update replaces the running kernel, deployment exits with code 75 before
AUR convergence and subsequent system configuration. Reboot and rerun the
update. Group changes require a new login session.

Home Manager installs `just` for shorter commands:

| Command | Purpose |
| --- | --- |
| `just check-fast` | Check source formatting, Python static errors, and declaration interfaces |
| `just check` | Run all source checks and build the managed home |
| `just build` | Build the deployment without activating it |
| `just arch-workstation` | Deploy using installed native packages |
| `just arch-workstation update` | Fully update native packages, then deploy |
| `just check-arch` | Query remote package inventories; requires connectivity |

Before `just` is installed, use `nix run .#just -- <recipe>`.

## Change the configuration

| Change | Edit |
| --- | --- |
| Login identity, groups, selected profiles and modules | [hosts/arch/users.nix](hosts/arch/users.nix) |
| Graphics, OpenRazer and initramfs requirements | [hosts/arch/hardware.nix](hosts/arch/hardware.nix) |
| Arch-native package inventory | [platforms/arch/packages.nix](platforms/arch/packages.nix) |
| Reusable CLI/development bundles | [profiles](profiles/default.nix) |
| User-specific Home Manager preferences | [homes/abnertu/home.nix](homes/abnertu/home.nix) |
| Shared home files and graphical unit policy | [modules/home](modules/home/default.nix) |
| Runner instances and resource limits | [hosts/arch/gitlab-runners.nix](hosts/arch/gitlab-runners.nix) |
| Arch convergence behavior | [platforms/arch/arch-switch.sh](platforms/arch/arch-switch.sh) |

Arch owns graphical executables, drivers and system services. Home Manager owns
CLI/development tools, static home files and user-unit policy; graphical units
call stable Arch paths. Do not install a second desktop executable through Home
Manager to change its configuration.

A deployment's profile is a label selected from its user's profiles. Deployment
activates **all** profiles and modules selected by that user; it does not switch
to an isolated profile. See [CONTEXT.md](CONTEXT.md) for composition terminology.

## Maintain the locked editor and desktop inputs

Neovim and Hyprland configuration are separate repositories locked by this flake.
Develop them outside their runtime paths, for example under `~/codebase`.

```bash
nix build --no-link --override-input hypr-config path:$HOME/codebase/hypr \
  '.#homeConfigurations."abnertu@arch".activationPackage'

# Adopt a published revision:
nix flake update hypr-config
nix flake check
```

Use `neovim-config` for the Neovim input. Neovim is linked as one directory;
Hyprland uses a writable directory containing recursive links. Activation rejects
Git worktrees at these targets and known adjacent backup paths. Resolve collisions
at their source; backup-extension flags are rejected by deployment wrappers.
Each managed skill is also linked as one directory.

## Optional Runner operations

Removing or emptying `gitlabRunners` in the Host omits the Runner controller and
its module dependencies from composition. It does not delete existing accounts,
registrations or containers. Normal workstation deployment never reconciles or
registers a Runner.

For instance setup, registration and live verification, follow
[the Runner operations guide](docs/runners.md). Each instance has one service
account, subordinate-ID allocation, rootless Podman socket and manager. Jobs
remain unprivileged, use concurrency one and receive no host socket.

## Develop and troubleshoot

Start with `just check-fast`, then run `nix flake check`. The checks include
GitHub workflow linting alongside
isolated Arch command tests, Runner validation and reconciliation tests, and
generated Home Manager units. Test data belongs beside its owner and must not
depend on real host registrations or credentials.

[GitHub Actions](.github/workflows/check.yml) runs these checks and builds the
deployment artifacts on pushes to `main`, pull requests and manual dispatch.
It uses an Ubuntu runner for Nix builds; it never activates the workstation or
runs live Runner operations. Action revisions are pinned to commit hashes.

New Nix inputs must be tracked before flake evaluation; stage only intended
paths. Use the locked formatter with `nix fmt -- path/to/file.nix`.
[AGENTS.md](AGENTS.md) contains the coding-agent contract.

For exit codes, pending actions, deployment locks and recovery behavior, see
[the deployment guide](docs/deployment.md). There is no automatic cleanup,
package removal, garbage collection, directory backup service or Runner purge.
