# Agent instructions

Read [CONTEXT.md](CONTEXT.md) before changing composition. `configuration.nix`
is the selected Host entry. Public options are typed and owned; Host baselines
use `lib.mkDefault`; user overrides use ordinary definitions. Never use import
order as precedence or accept unknown fields.

Ownership is exclusive: `lib/` evaluates and composes, `hosts/` selects identity
and hardware, `platforms/arch/` owns native packages and services,
`modules/` owns capabilities, and `profiles/`/`homes/` own Home Manager state.
Service accounts never receive a human home composition.

Core deployment failures stop immediately. Optional readiness may skip only when
preparation has never completed; invalid receipts, checksum drift, conflicts,
command failures and runtime drift are errors. Verbose mode reaches Nix and
privileged adapters with complete diagnostics. Routine runs never install
packages; only `--update` performs pacman/AUR convergence. Preserve kernel gates,
locks, pending markers and idempotence. Explicit `--purge` removes managed Arch
state while preserving packages and mutable application data.

AI preparation must match the declared source selector, receipt and every model
identity/checksum before services converge. llama-swap, llama-server and Caddy
remain loopback-only. Runner instances remain outside workstation deployment;
tokens never enter Git, derivations or unredacted logs.

Never read or print credentials, private keys, KeePassXC databases, Runner tokens,
Noctalia keys or mutable application data. Keep UWSM as the Hyprland entry point,
one startup owner per application, and project source trees outside managed paths.

Use temporary paths, fake native commands and isolated VMs. Prefer contract tests
over inventory assertions. Run `just check-fast`, `just check`, `just build`, the
Home Manager activation build and `git diff --check` for composition or adapter
changes. Keep README as the entry point and docs limited to current procedures.
