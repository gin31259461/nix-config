# AGENTS Instructions

Work in this operator-controlled Arch Linux checkout. Read [CONTEXT.md](CONTEXT.md) before changing composition logic and the relevant guide in [`docs/`](docs/) before editing a feature. Keep package and service inventories in their owning Nix sources, never in these instructions.

## Ownership and evaluation

- `configuration.nix` imports the selected Host. Put typed public options in `lib/configuration-options.nix` or a feature interface under `modules/`; normalize through `lib/eval-configuration.nix`.
- Host baselines use `lib.mkDefault`; user overrides use ordinary definitions. Reject unknown fields, invalid types and invalid combinations. Never use import order to set precedence.
- Give each resource one owner: `lib/` for evaluation and composition, `hosts/` for identity and defaults, `platforms/arch/` for native realization, `modules/` for capabilities, and `profiles/` or `homes/` for Home Manager composition. Keep registries explicit.
- Keep static, public policy in Nix-generated artifacts. Keep Python and Bash adapters focused on safe live-state reconciliation, validation and recovery. Do not put secrets, runtime receipts, registration tokens or mutable application data into derivations.
- Human accounts must exist before deployment. Modules own service accounts; those accounts receive no human home composition. Do not bump Home Manager `stateVersion` during routine updates.

## Deployment contracts

- Build the exact Home Manager activation package into the deployment artifact. Complete Arch convergence before activating it; do not reevaluate a different home at runtime. The stages do not share a rollback transaction.
- Core failures stop immediately. An optional `not ready` skip is allowed only when required preparation has never completed. Invalid receipts, checksum drift, ownership conflicts, missing declared core hardware, command failures and runtime drift are errors, including a readiness change after preflight.
- Routine runs never install packages; only `--update` performs pacman/AUR convergence. Preserve kernel gates, locks and pending markers. Record intent before mutation, clear it only after success, and avoid rewriting unchanged files or restarting healthy services.
- Preserve command failure diagnostics, including stdout, stderr and partial timeout output, while redacting secrets. Verbose mode must reach Nix, Home Manager and privileged adapters.
- Disabling an Arch declaration withdraws management without authorizing removal or cleanup. Explicit `--purge` removes managed Arch deployment state, preserves packages, accounts, Runner registrations and mutable data, and skips Home Manager. Do not add automatic cleanup, directory backups, garbage collection or Runner purge.
- AI preparation verifies the declared source selector, build receipt and every model identity/checksum before services converge. Prepared binaries and models stay outside the store; llama-swap, llama-server and Caddy stay loopback-only. Runner reconciliation, registration and verification remain separate from workstation deployment.

## Protected state and desktop

**Never read or print credentials, private keys, password stores, Runner tokens, Noctalia keys or mutable application data.** Keep them outside Git and derivations. Tokens must not appear in command arguments or unredacted logs; use synthetic fixtures. Keep UWSM as the Hyprland entry point and one startup owner per application. Pass (`programs.password-store`) owns normal user credential storage. Develop Hyprland and Neovim source outside managed runtime paths and adopt published revisions through intentional lock updates.

## Validation and documentation

Use temporary paths, fake native commands and isolated VMs; test behavior rather than copying inventories into assertions. For composition or adapter changes, run from the repository root:

```bash
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

These commands build source without activation. Deployment, preparation, registration, package installation and service operations affect live state and are not documentation checks. For documentation-only edits, check Markdown syntax, relative links and `git diff --check`.

Keep [README.md](README.md) as the entry point, [CONTEXT.md](CONTEXT.md) as the composition model and `docs/` as current operator procedures. Update the relevant guide when public behavior changes. Keep agent constraints here rather than duplicating runbooks.
