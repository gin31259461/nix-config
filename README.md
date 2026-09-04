# nix-config

[![Arch Linux](https://img.shields.io/badge/Arch_Linux-native-1793D1?logo=archlinux&logoColor=white)](https://archlinux.org/)
[![Nix Flakes](https://img.shields.io/badge/Nix-Flakes-5277C3?logo=nixos&logoColor=white)](https://nix.dev/concepts/flakes.html)
[![Home Manager](https://img.shields.io/badge/Home_Manager-26.05-7EBAE4?logo=nixos&logoColor=white)](https://github.com/nix-community/home-manager/tree/release-26.05)

Declarative configuration for Abner's Arch workstation and future NixOS hosts.
The flake combines machine identity, reusable profiles, optional modules, Home
Manager policy, and small platform adapters while keeping every package, file,
account, and service under one owner.

The active deployment is `arch-workstation`: host `arch`, profile
`workstation`, login user `abnertu`, and Home Manager configuration
`abnertu@arch`. No NixOS host is fabricated; a real host must supply its own
hardware and filesystem configuration.

## Deploy the Arch workstation

Arch owns Nix itself, graphical/session executables, drivers, PAM, polkit, and
system services. Install Nix through pacman, start the daemon, and make `yay`
available before the first deployment:

```bash
sudo pacman -S --needed nix
sudo systemctl enable --now nix-daemon.service
exec "$SHELL" -l
nix --version
yay --version
```

The tracked `nix.conf` enables flakes through
`$XDG_CONFIG_HOME/nix/nix.conf`. From this repository, validate and perform the
first deployment with a full Arch update:

```bash
nix run .#just -- check
nix run .#just -- arch-workstation update
```

Home Manager installs `just`, so routine deployments are shorter:

```bash
just arch-workstation
```

Routine deployment does not install or update packages. It verifies the
declared Arch, LizardByte, and AUR inventories, then refuses to continue if a
declared package is missing. Install missing packages and update the system
safely with an explicit full upgrade:

```bash
just arch-workstation update

# Equivalent flake app invocation:
nix run .#arch-workstation -- --update
```

The update path installs the managed LizardByte repository include, runs a
complete `pacman -Syu` with the declared official and LizardByte packages, then
converges the declared AUR packages. Its signature exception applies only to
`[lizardbyte]`, beta repositories are not enabled, and Sunshine is addressed as
`lizardbyte/sunshine`.

If an update replaces the running kernel, deployment stops before
module-dependent configuration and requests a reboot. Boot the new kernel and
rerun the same command; DKMS owns rebuilding OpenRazer for the installed kernel.

After the Arch plane succeeds, Home Manager activates CLI/development packages,
static home configuration, locked Hyprland and Neovim inputs, and custom user
unit policy. The deployment performs no cleanup, garbage collection, directory
backup, Runner registration, or repository retirement.

> [!IMPORTANT]
> Home Manager intentionally activates without a backup-file extension. When a
> path collides, reconcile that path with its owner; do not add `-b` or
> `--backup-file-extension`, because adjacent backups can enter runtime
> discovery.

## Project commands

| Command | Result |
| --- | --- |
| `just check` | Evaluate and build every flake check |
| `just check-arch` | Resolve native package inventories |
| `just build arch-workstation` | Build the deployment without activation |
| `just arch-workstation` | Converge the host without updating system packages |
| `just arch-workstation update` | Update packages, then converge the host |
| `nix build .#runnerctl` | Build the GitLab Runner controller |

`arch-switch`, Home Manager activation, and Runner reconciliation are live
operations. Builds and checks are the safe review path.

## Composition

| Layer | Responsibility |
| --- | --- |
| `hosts/<name>/` | Machine identity, selections, users, and instance values |
| `platforms/` | OS realization and native package ownership |
| `profiles/` | Reusable general-purpose Home Manager bundles |
| `homes/<user>/` | Personal Home Manager differences |
| `modules/home/` | Shared user capabilities and graphical-session policy |
| `modules/nixos/` | Reusable NixOS capabilities |
| `modules/gitlab-runner/` | Runner policy, controller, and invariant checks |

The vocabulary is defined in [CONTEXT.md](CONTEXT.md). Host `arch` selects the
`base`, `dev`, and `workstation` profiles plus the `hyprland` and
`graphical-session` modules. Registries in `profiles/default.nix` and
`modules/home/default.nix` keep those imports explicit.

Graphical applications are Arch packages. Home Manager owns their configuration
and user-unit policy but invokes executables through stable system paths, so
desktop files, systemd units, GPU integration, and singleton behavior refer to
the same installation. UWSM remains the only Hyprland session entrypoint.

## Locked external configuration

Hyprland and Neovim are locked non-flake inputs named `hypr-config` and
`neovim-config`. Develop them in their own worktrees at `~/codebase/hypr` and
`~/codebase/orbitvim`, not in active runtime paths.

Test a local revision without changing `flake.lock`:

```bash
nix build --override-input hypr-config path:$HOME/codebase/hypr \
  '.#homeConfigurations."abnertu@arch".activationPackage'
nix build --override-input neovim-config path:$HOME/codebase/orbitvim \
  '.#homeConfigurations."abnertu@arch".activationPackage'
```

After publishing an upstream revision, adopt it explicitly:

```bash
nix flake update hypr-config
nix flake update neovim-config
just build arch-workstation
```

Neovim is linked as one directory. Hyprland is projected recursively into a
clean, writable, non-VCS directory so generated state and selected profiles can
change without exposing migration backups or repository metadata.

## GitLab Runner

The Arch host declares `frontend` and `dotnet` instances in
`hosts/arch/gitlab-runners.nix`. Each owns a dedicated account, home,
subordinate-ID range, rootless Podman socket, manager container, and
registration. Job containers remain unprivileged, have concurrency one, and do
not receive the host Podman socket.

Build the controller and address one exact instance at a time:

```bash
runnerctl_path="$(nix build --no-link --print-out-paths .#runnerctl)"
sudo "$runnerctl_path/bin/runnerctl" status frontend
sudo "$runnerctl_path/bin/runnerctl" reconcile frontend
sudo "$runnerctl_path/bin/runnerctl" verify frontend
```

Repeat for `dotnet`. `network.requiredInterface` is a readiness check only; it
does not force routing through that interface. Reconciliation preserves an
existing single-runner registration without printing its metadata.

Register a new instance by passing its authentication token only through the
environment:

```bash
read -rsp 'GitLab Runner token: ' GITLAB_RUNNER_TOKEN
export GITLAB_RUNNER_TOKEN
sudo --preserve-env=GITLAB_RUNNER_TOKEN \
  "$runnerctl_path/bin/runnerctl" register frontend
unset GITLAB_RUNNER_TOKEN
```

There is intentionally no purge command. A NixOS host can import the same
interface through `nixosModules.gitlab-runner`.

## Validation and migration

Use `nix flake check` for normal repository changes. Build the affected Home
Manager activation package when its closure or generated units change:

```bash
nix build '.#homeConfigurations."abnertu@arch".activationPackage'
```

Runner `status` and `verify` inspect external state and connectivity, so they
are not part of source-only validation. The remaining Runner adoption and
legacy repository retirement gates live in
[the migration guide](docs/migrations/from-dotfiles-homebase.md).
