# Composition model

The flake connects machine choices to Arch realization and Home Manager
configuration. These terms describe the current implementation.

| Term | Meaning |
| --- | --- |
| Host | A machine's identity, login users, hardware and selected capabilities |
| Platform | The operating-system realization mechanism; currently x86_64 Arch |
| Profile | A reusable general-purpose Home Manager bundle |
| Module | A capability with one interface and its implementation, including internal platform adapters when needed |
| Adapter | The implementation that realizes declared policy on a particular platform |
| Login user | A human account declared by a Host and provisioned before deployment |
| Service account | A non-human identity created and owned by its Module |
| Instance | One configured occurrence of a Module on a Host |
| Deployment target | A named Arch-then-home workflow for one Host and login user |
| Required interface | A network readiness prerequisite, not a routing or egress policy |

## Selection and realization

`flake.nix` explicitly selects `configuration.nix` through
`lib/eval-configuration.nix`. The entry imports Host modules and accepts ordinary
user overrides. `lib/configuration-options.nix` composes typed namespaces;
capability-owned schemas remain in their Modules. Host baselines use `mkDefault`.
The module system merges imports and validates option names/types; the evaluator
normalizes the result into private Host/adapter values and retains identity
validation. `configurations.arch` exposes resolved public values for inspection.

Registries in `profiles/default.nix` and `modules/home/default.nix` enumerate
available home selections. Each selection has a default-on enable switch; no
Host or overlay is discovered by scanning directories. Per-user `home` is a
deferred Home Manager module, preserving that module system's own merge rules.

A deployment is named `<host>-<profile>`. Its profile is a descriptive label
that must occur in the selected user's profile list. The target activates that
user's entire composed Home Manager configuration, including all selected
profiles and modules. Profiles are not mutually exclusive deployment modes.

The Host supplies hardware intent. The Arch adapter selects native packages
from that intent and combines them with optional Module dependencies.
Application instances remain private to their Module and Host declaration.

The Host selects `programs.ai` and `virtualisation` through typed default-on
parent and child enable switches. AI exports an explicit pinned native-build
and model preparation command, a reviewed model inventory with per-model
runtime presets, and an optional
Caddy/Tailscale Serve adapter, Codex AUR requirements and a shared Home Manager
module for skill presets. The AI adapter
owns its service policy and loopback proxy while reusing Arch's Tailscale owner.
Until the selected build and model are explicitly prepared, that adapter
withdraws from native convergence without blocking the rest of the deployment.
Virtualization exports native package requirements and login
groups for QEMU/KVM and Podman use. Its optional KVM GUI also exports the local
libvirt socket for Arch to converge. Arch realizes these values; Runner
requirements remain independent of the login-user virtualization selection.

The public `networking`, `i18n`, `time`, `console` and `services` namespaces
select system behavior with default-on enable switches. Disabled capabilities
normalize to private unmanaged `systemSettings` values. Shared system option
types and invariants live in `lib/system-settings-options.nix` and
`lib/system-settings.nix`; `platforms/arch/system/` owns
Arch rendering, preflight and convergence. The Arch service inventory owns
workstation service policy; Module units retain their existing owners.
The controller holds one deployment lock across both preflight and mutation.
System settings never belong to Home Manager or reusable Profiles.
The Host also selects a prepared Wi-Fi hotspot under `networking.hotspot`. Arch
adopts its public NetworkManager settings and derives scoped UFW exceptions;
NetworkManager retains credentials and NAT ownership. NetworkManager selection
gates hotspot management, and firewall selection gates its UFW contributions.

The Runner Module accepts zero or more enabled instances under
`services.gitlabRunner`. Its parent and instance enables default to true; an
empty instance set remains empty. With zero instances, it
exports no controller app/package or native requirements; its independent
interface and fake-runtime tests remain available.

## State and ownership

Nix builds desired artifacts. Arch deployment compares those artifacts with
managed system files and runtime state; Home Manager performs home activation.
The deployment artifact fixes the Home Manager generation before either stage
runs. Activation uses Home Manager's profile-managing driver rather than
resolving the source again. The two stages are ordered but do not share a
rollback transaction.

A successful repeat deployment with unchanged declarations and healthy runtime
state leaves managed file contents and service processes unchanged. Runtime
drift can still require repair. Pending-action markers preserve unfinished
work across failures; they are mutable host state, not repository inputs.

Disabling or removing a declaration is not authorization to retire an account, remove
packages or erase application state. Those operations are intentionally outside
the deployment interface.

Use these distinctions consistently: a Host is not a Platform, a Module is not
a Profile, and a service account is not a login user. Operator workflows live in
[README.md](README.md); agent decisions live in [AGENTS.md](AGENTS.md).
