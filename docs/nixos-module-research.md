# NixOS configuration patterns

Research date: 2026-09-07. This note records design evidence and recommendations;
[configuration.md](configuration.md) documents the implemented interface.

## Official patterns

NixOS uses a `configuration.nix` module as a readable entry point, with explicit
`imports` for other modules. Related settings share namespaces such as
`networking.hostName`, `time.timeZone`, `users.users` and `services.openssh`.
The flake selects that module explicitly. This provides a useful configuration
shape for this repository without changing its Arch operating-system ownership.
[Official configuration overview](https://wiki.nixos.org/wiki/NixOS_system_configuration)

The Nixpkgs module system is a general configuration library offering types,
composition and documentation. `lib.evalModules` merges modules and returns
both `config` values and `options` declarations. A custom module `class` rejects
imports carrying a different class. `specialArgs` can supply import-time
arguments; `_module.args` becomes available after imports resolve. Custom
helpers should have their own argument name instead of replacing `lib`.
[Nixpkgs module-system reference](https://nixos.org/manual/nixpkgs/stable/#module-system)

`mkEnableOption` creates a boolean option whose default is **false**. For the
requested default-on capabilities, declare a boolean `mkOption` with
`default = true` and a description, or override the helper's returned default.
This is a repository policy choice, not NixOS's universal enable convention.
[Nixpkgs option implementation](https://github.com/NixOS/nixpkgs/blob/master/lib/options.nix)

Option defaults have priority 1500, `mkDefault` definitions 1000, ordinary
assignments 100, and `mkForce` 50; lower numbers win. Import ordering therefore
does not implement “last file wins.” Use ordinary assignments for reviewed
host overrides and `mkDefault` for overridable baseline definitions. Use
`mkForce` deliberately when replacing merged collections. `mkIf` delays
conditions on `config`, avoiding recursion in conditional module definitions;
`mkMerge` combines definition sets. Types and assertions express configuration
constraints before building or deployment.
[NixOS module-writing manual](https://nixos.org/manual/nixos/stable/#sec-writing-modules)

The implementation also supplies alias helpers that preserve definition
properties, and removed-option helpers with migration diagnostics. Reassigning
an already evaluated value loses its original override priority. A clean public
interface should therefore have one canonical option owner and avoid multiple
independently evaluated copies of the same public option.
[Nixpkgs module implementation](https://github.com/NixOS/nixpkgs/blob/master/lib/modules.nix)

## Application to this repository

These are design recommendations inferred from the sources above and the
repository's [composition model](../CONTEXT.md):

- Give the selected Host one `configuration.nix` entry point. Keep reusable
  option declarations and defaults separate from reviewed instance values.
- Evaluate a typed public configuration once. Normalize it at the boundary
  into the existing Arch and Home Manager adapters; avoid moving runtime
  convergence or security policy into the flake.
- Group identity and firewall under `networking`, localization under `i18n`,
  clock settings under `time`, system services under `services`, portable
  applications under `programs`, and virtualization under `virtualisation`.
  Namespaces communicate ownership; matching a NixOS spelling does not imply
  support for all upstream NixOS options.
- Expose meaningful optional capabilities through boolean `enable` options
  defaulting to true. Parent switches must suppress child contributions even
  when child defaults are true. Inventory, generated files and unit
  relationships must agree on the effective selection.
- Keep required identity, platform, user and instance values typed. They do
  not need artificial enable switches. Keep fixed Runner isolation policy
  internal; an enabled Runner capability with no instances remains empty.
- Treat disabled Arch contributions as unmanaged state under the existing
  live-state boundary. Do not interpret an option becoming false as permission
  to remove packages, retire accounts or delete application data. Describe
  Home Manager's managed-generation removal separately from Arch behavior.
- Validate default values, normal overrides, imports, list replacement,
  invalid names/types, parent-child disabling and dependency combinations
  using source-only fixtures. Retain the existing fake-runtime recovery tests.

Do not import the NixOS service implementation wholesale: this repository's
Arch adapter owns native executables and services, while Home Manager owns its
existing portable and user-unit responsibilities. Configuration ergonomics can
be shared while those deployment boundaries remain explicit.
