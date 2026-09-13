# nix-config

[![Checks](https://github.com/gin31259461/nix-config/actions/workflows/check.yml/badge.svg)](https://github.com/gin31259461/nix-config/actions/workflows/check.yml)

Declarative Arch Linux workstation configuration built with Nix and Home Manager.
Arch owns native packages, system files, services, kernel integration and host
policy. Home Manager owns portable user packages, static files and user services.

![Desktop preview](docs/assets/preview.png)

## Use

The selected host is [configuration.nix](configuration.nix). It imports
`hosts/arch`, whose values are defaults; ordinary definitions in the selected
entry override them. The typed public options are defined in
`lib/configuration-options.nix` and invalid or unknown fields fail evaluation.

Inspect the normalized configuration with:

```bash
nix eval .#lib.configurations.arch.networking.hostName
nix eval --json .#lib.configurations.arch.networking.firewall
```

Routine convergence checks the existing Arch installation and activates the
built Home Manager generation:

```bash
just arch-workstation
```

Use `update` only when package installation or upgrades are intended. Use
`verbose` to pass diagnostics to Nix and privileged adapters:

```bash
just arch-workstation update verbose
```

Optional AI assets are prepared separately and remain outside the Nix store:

```bash
just prepare-ai
just prepare-ai build
just prepare-ai model
```

GitLab Runner instances have an independent lifecycle:

```bash
just prepare-runner frontend
GITLAB_RUNNER_TOKEN=glrt-... just initialize-runner frontend
just verify-runner frontend
```

Registration tokens are read from the environment and are never stored in Git,
Nix derivations or unredacted logs.

## Development

Nix supplies the development interpreter and tools; Python dependencies and
Ruff configuration are declared in [pyproject.toml](pyproject.toml).

```bash
nix develop
just check-fast
just check
just build
```

Checks use temporary paths, fake native commands and isolated VMs. They do not
modify the workstation. Build the Home Manager activation package directly with:

```bash
nix build --no-link '.#homeConfigurations."abnertu@arch".activationPackage'
```

## Ownership

`lib/` evaluates and normalizes the typed schema. `hosts/` contains machine
identity and defaults. `platforms/arch/` contains Arch adapters. `modules/`
contains capability interfaces and implementations. `profiles/` and `homes/`
compose Home Manager state. `checks/` contains isolated validation and `docs/`
contains current operator runbooks. The composition model is documented in
[CONTEXT.md](CONTEXT.md); agent constraints are in [AGENTS.md](AGENTS.md).

Disabled capabilities withdraw management and do not remove existing packages,
services, registrations or application data. See the relevant runbook under
[`docs/`](docs/) for preparation, deployment and recovery details.
