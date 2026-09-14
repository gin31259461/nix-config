# AGENTS Instructions

Read [CONTEXT.md](CONTEXT.md) before changing composition. Work in this checkout
and read scoped instructions before editing their files. Keep package and
service inventories in their owning source, not in agent instructions.

## Composition and ownership

`configuration.nix` imports the selected Host. Define typed public options in
`lib/configuration-options.nix` or the owning capability interface and normalize
them through `lib/eval-configuration.nix`. Reject unknown fields, invalid types
and invalid combinations. Host baselines use `lib.mkDefault`; user overrides use
ordinary definitions. Never use import order as precedence.

Keep ownership exclusive: `lib/` evaluates and composes; `hosts/` selects identity,
users, hardware and capability defaults; `platforms/arch/` owns native packages
and system services; `modules/` owns capabilities; `profiles/` and `homes/` own
Home Manager composition. Give each package, account, file and service one owner.
Keep profile and home-module registries explicit rather than discovering modules
from directory contents.

Human accounts must exist before deployment. Service accounts belong to their
modules and never receive a human home composition. Do not bump Home Manager
`stateVersion` during routine updates.

## Deployment contracts

Build the Home Manager activation package into the deployment artifact. Complete
Arch convergence before activating that exact generation; do not reevaluate or
substitute a different home at runtime. The stages do not share a rollback
transaction.

Core failures stop immediately. Optional readiness may return the dedicated
`not ready` status only when required preparation has never completed; report
that state as a highlighted skip. Invalid receipts, checksum drift, ownership
conflicts, command failures and runtime drift are errors, never skips.

Routine runs never install packages; only `--update` performs pacman/AUR
convergence. Preserve kernel gates, locks, pending markers and idempotence.
Record pending actions before mutation and clear them only after success. Do not
rewrite unchanged files, restart healthy services or discard recovery markers
to make a retry pass. Verbose mode must reach Nix, Home Manager and privileged
adapters. Preserve complete command failure diagnostics, including stdout,
stderr and partial timeout output, while redacting secrets.

Disabling an Arch declaration withdraws management without authorizing package
removal, service retirement, account or registration deletion, or data cleanup.
Home Manager uses its normal generation lifecycle. Explicit `--purge` removes
managed Arch deployment state while preserving packages, accounts, Runner
registrations and mutable application data; it skips Home Manager activation.
Do not add automatic cleanup, directory backups, garbage collection or Runner
purge to workstation deployment.

AI preparation must verify the declared source selector, build receipt and every
model identity/checksum before services converge. Keep prepared binaries and
models outside the Nix store. llama-swap, llama-server and Caddy remain
loopback-only. Runner reconciliation, registration and verification remain a
separate lifecycle outside workstation deployment.

## Protected state and desktop

Never read or print credentials, private keys, KeePassXC databases, Runner tokens,
Noctalia keys or mutable application data. Keep secrets and mutable runtime state
outside Git and Nix derivations; tokens must never appear in command arguments
or unredacted logs. Use synthetic fixtures when investigating these paths.

Keep UWSM as the Hyprland entry point and one startup owner per application.
Keep project source trees outside managed paths, including Hyprland and Neovim
runtime configuration. Adopt their published revisions through intentional
flake lock updates.

## Validation and documentation

Use temporary paths, fake native commands and isolated VMs. Prefer tests of
behavioral contracts over assertions that merely repeat production inventories.
For composition or adapter changes, run:

```bash
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

These commands validate and build source without activation. Deployment,
preparation, registration, package installation and service operations affect
live state and require that state to be within the user's task. Do not use them
to validate documentation. For documentation-only edits, check Markdown,
relative links and `git diff --check`.

Keep [README.md](./README.md) as the entry point, [CONTEXT.md](CONTEXT.md) as the
composition model, and `docs/` limited to current operator procedures. Update
the relevant documentation when public behavior changes; keep agent constraints
here instead of duplicating runbooks.
