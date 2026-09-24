# Composition model

This repository describes one existing Arch Linux workstation with a Nix-evaluated policy and two realization layers. Nix builds an immutable deployment artifact containing the selected Home Manager activation package. Arch adapters reconcile native files, packages and services before that exact home generation activates.

| Boundary | Owner | Responsibility |
| --- | --- | --- |
| Public configuration | `configuration.nix`, `lib/configuration-options.nix`, feature interfaces in `modules/` | Typed options, defaults and validation |
| Host | `hosts/` | Identity, users, hardware and capability baselines |
| Native platform | `platforms/arch/` | Arch packages, generated policy, privileged reconciliation |
| Home | `profiles/`, `homes/`, home modules | User packages, managed static files and user services |
| External runtime | Operator and feature preparation commands | Secrets, mutable data, native builds and model downloads |

`configuration.nix` imports the selected Host. Host baselines use `lib.mkDefault`, so ordinary user definitions override them without depending on import order. `lib/eval-configuration.nix` normalizes the typed result for private consumers. Registries are explicit. One package, account, file or service should have one owner.

## Static policy and live reconciliation

Nix generates fixed content such as Home Manager files, systemd units, drop-ins, AI router/Caddy policy and Runner templates. Native adapters remain responsible for operations that depend on the current machine: safe adoption of existing files, ownership and permission checks, account and service state, locks, pending markers, package operations and failure reporting. Runner token metadata is merged into its Nix-generated public template only at runtime; neither tokens nor mutable registrations enter a derivation.

This separation borrows the declarative file-rendering idea from [nix-maid](https://viperml.codeberg.page/nix-maid/api.html) without adding it as a dependency or a second Home Manager layer. The existing feature modules own generated artifacts, and adapters retain Arch-specific reconciliation.

Home Manager commonly realizes static home files through links to the store. Arch-native files are copied or merged into `/etc` with native ownership and mode, while prepared llama.cpp binaries and GGUF models stay outside the store. Hyprland and Neovim source trees also stay outside managed runtime paths: by default they are pinned as external flake inputs, or can be projected from local worktrees using user `development` options (`development.neovimPath`, `development.hyprlandPath`) via out-of-store symlinks.

## Deployment lifecycle

1. Build the deployment artifact and its exact Home Manager generation.
2. Preflight Arch identity, packages, core native state and optional readiness.
3. Converge packages only when `--update` is selected, then native files and services.
4. Converge prepared optional modules.
5. Activate the fixed home generation.

Core failures stop the run. Optional `not ready` applies only before preparation has ever completed; invalid receipts, checksum drift, ownership conflicts, command failures and later runtime drift are errors. Arch and Home Manager do not share a rollback transaction. Pending markers are recorded before native mutation and retained until successful completion. Disabling an Arch declaration withdraws management; explicit purge has the narrower scope documented in [deployment](docs/deployment.md).

AI preparation and Runner registration are separate lifecycles. The [AI guide](docs/ai.md) and [Runner guide](docs/runners.md) own their operator procedures. [AGENTS.md](AGENTS.md) owns change constraints; [README.md](README.md) is the entry point.
