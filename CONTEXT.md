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

`flake.nix` explicitly imports a Host, validates it, constructs its users' Home
Manager configurations, and builds the selected deployment target. Registries
in `profiles/default.nix` and `modules/home/default.nix` resolve named selections.
Nothing discovers Hosts or loads overlays by scanning directories.

A deployment is named `<host>-<profile>`. Its profile is a descriptive label
that must occur in the selected user's profile list. The target activates that
user's entire composed Home Manager configuration, including all selected
profiles and modules. Profiles are not mutually exclusive deployment modes.

The Host supplies hardware intent. The Arch adapter selects native packages
from that intent and combines them with optional Module dependencies.
Application instances remain private to their Module and Host declaration.

The Host also selects AI and virtualization through typed parent and child
enable switches. AI exports AUR requirements and a shared Home Manager module
for skill presets. Virtualization exports native package requirements and login
groups for QEMU/KVM and Podman use. Its optional KVM GUI also exports the local
libvirt socket for Arch to converge. Arch realizes these values; Runner
requirements remain independent of the login-user virtualization selection.

The Runner Module accepts zero or more instances. With zero instances, it
exports no controller app/package or native requirements; its independent
interface and fake-runtime tests remain available.

## State and ownership

Nix builds desired artifacts. Arch deployment compares those artifacts with
managed system files and runtime state; Home Manager performs home activation.
The two stages are ordered but do not share a rollback transaction.

A successful repeat deployment with unchanged declarations and healthy runtime
state leaves managed file contents and service processes unchanged. Runtime
drift can still require repair. Pending-action markers preserve unfinished
work across failures; they are mutable host state, not repository inputs.

Removing a declaration is not authorization to retire an account, remove
packages or erase application state. Those operations are intentionally outside
the deployment interface.

Use these distinctions consistently: a Host is not a Platform, a Module is not
a Profile, and a service account is not a login user. Operator workflows live in
[README.md](README.md); agent decisions live in [AGENTS.md](AGENTS.md).
