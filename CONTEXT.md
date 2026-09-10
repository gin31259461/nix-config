# Composition model

This repository declares one Arch workstation and realizes it through Nix-built
adapters plus Home Manager. These terms describe the current implementation.

| Term | Meaning |
| --- | --- |
| Host | Machine identity, users, hardware and selected capabilities |
| Platform | Native realization layer; currently x86_64 Arch Linux |
| Profile | Reusable Home Manager bundle |
| Module | Capability with one interface and one owner |
| Adapter | Platform-specific implementation of declared policy |
| Core module | Required deployment behavior; missing prerequisites fail deployment |
| Optional module | Independently selected behavior that may require explicit preparation |
| Instance | One configured occurrence of a module, such as a GitLab Runner |
| Deployment | Ordered Arch convergence followed by one fixed Home Manager generation |

## Configuration flow

`configuration.nix` imports the selected Host. `lib/configuration-options.nix`
defines the typed public schema. `lib/eval-configuration.nix` evaluates that
schema and normalizes it into private Host and adapter values. `flake.nix` wires
those values into packages, apps, Home Manager configurations and checks.

Host values are defaults. User overrides are ordinary Nix module definitions;
import order is not precedence. Profiles and home modules are explicit
registries, not directory discovery.

## Realization flow

The deployment artifact fixes the Home Manager activation package at build time.
Runtime execution is ordered as follows:

1. Validate the Arch host, login user, package state and core prerequisites.
2. Preflight core system settings.
3. Evaluate optional native module readiness.
4. Apply requested package updates when `--update` is selected.
5. Converge Arch system settings, native files and services.
6. Converge prepared optional native modules.
7. Activate the exact built Home Manager generation.

Core failures stop immediately. An enabled optional module may return a dedicated
`not ready` status only when its required preparation has never completed. The
controller reports that state as a highlighted skip and continues. Ownership
conflicts, invalid receipts and runtime failures are errors, not skips.

The AI module follows this contract: `llama-prepare` owns the external llama.cpp
build and GGUF model preparation; the Arch AI adapter owns service, Caddy and
Tailscale Serve convergence after those assets are ready.

GitLab Runner instances use their own `runnerctl` lifecycle and are intentionally
outside workstation deployment. Reconcile prepares host/runtime state; register
initializes the GitLab registration; verify checks the resulting instance.

## Ownership

Arch owns native package installation, `/etc` policy, system services, kernel and
network integration. Home Manager owns user packages, static home files and user
services. Feature modules own their private configuration and runtime adapters.
One managed resource should have one owner.

Disabling a declaration withdraws desired management. It does not authorize
package removal, service retirement, account deletion, registration deletion or
application-data cleanup. Mutable runtime state and credentials never belong in
the Nix store or repository.

Operator commands are documented in [README.md](README.md) and `docs/`. Agent
change constraints are in [AGENTS.md](AGENTS.md).
