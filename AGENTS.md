# AGENTS Instructions

You are acting on an operator-controlled, existing-machine Arch Linux repository. Read [CONTEXT.md](CONTEXT.md) before changing any composition logic. Work within this checkout and read scoped documentation under `docs/` before editing corresponding feature modules.

**CRITICAL RULE:** Keep package and service inventories in their owning source files. Never duplicate inventories or application configuration inside these agent instructions.

## 1. Composition and Ownership Rules

- **Source of Truth:** `configuration.nix` imports the selected Host. Typed public options belong in `lib/configuration-options.nix` or the feature's capability interface under `modules/`. Normalization happens through `lib/eval-configuration.nix`.
- **Precedence:** Reject unknown fields, invalid types, and invalid combinations. Host baselines **must** use `lib.mkDefault`; user overrides in `configuration.nix` use ordinary definitions. **Never use import order as a precedence mechanism.**
- **Exclusive Ownership:** Give each package, account, file, and service **exactly one owner**:
  - `lib/`: Typed evaluation, normalization, and deployment composition.
  - `hosts/`: Host identity, users, hardware, and capability defaults.
  - `platforms/arch/`: Native packages, adapters, and system services.
  - `modules/`: Capability interfaces and their implementations.
  - `profiles/`, `homes/`: Reusable and user-specific Home Manager composition. Keep registries explicit (no directory-discovery magic).
- **Accounts:** Human accounts must exist before deployment. Service accounts belong to their modules and never receive a human home composition. Do not bump the Home Manager `stateVersion` during routine updates.

## 2. Deployment Contracts

- **Static Generation:** Build the Home Manager activation package into the deployment artifact. Complete Arch convergence **before** activating that exact generation. Do not reevaluate or substitute a different home at runtime. The Arch and Home Manager stages do not share a rollback transaction.
- **Error Handling:** Core failures stop immediately. Optional readiness may return the dedicated `not ready` status **only** when required preparation has never completed; report that state as a highlighted skip. **Invalid receipts, checksum drift, ownership conflicts, command failures, and runtime drift are errors, never skips.**
- **Mutation and Idempotence:** Routine runs never install packages; only `--update` performs pacman/AUR convergence. Preserve kernel gates, locks, pending markers, and idempotence. Record pending actions before mutation and clear them only after success. Do not rewrite unchanged files, restart healthy services, or discard recovery markers to make a retry pass.
- **Diagnostic Transparency:** Verbose mode must reach Nix, Home Manager, and privileged adapters. Preserve complete command failure diagnostics, including stdout, stderr, and partial timeout output, while redacting secrets.
- **Cleanup and Purge:** Disabling an Arch declaration withdraws management without authorizing package removal, service retirement, account/registration deletion, or data cleanup. Explicit `--purge` removes managed Arch deployment state while preserving packages, accounts, Runner registrations, and mutable application data; it skips Home Manager activation. **Do not add automatic cleanup, directory backups, garbage collection, or Runner purge to workstation deployment.**
- **AI and External Dependencies:** AI preparation must verify the declared source selector, build receipt, and every model identity/checksum before services converge. Keep prepared binaries and models outside the Nix store. llama-swap, llama-server, and Caddy remain loopback-only. Runner reconciliation, registration, and verification remain a separate lifecycle outside workstation deployment.

## 3. Protected State and Desktop Constraints

- **Absolute Secret Safety:** **Never read or print credentials, private keys, password stores, Runner tokens, Noctalia keys, or mutable application data.** Keep secrets and mutable runtime state outside Git and Nix derivations. Tokens must never appear in command arguments or unredacted logs. Use synthetic fixtures when investigating these paths.
- **Desktop Strategy:** Keep UWSM as the Hyprland entry point and one startup owner per application. Pass (`programs.password-store`) provides standard user credential storage. Keep project source trees outside managed paths, including Hyprland and Neovim runtime configuration. Adopt their published revisions through intentional flake lock updates.

## 4. Validation and Documentation

Use temporary paths, fake native commands, and isolated VMs. Prefer tests of behavioral contracts over assertions that merely repeat production inventories. For composition or adapter changes, run:

```bash
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

- **Runtime Avoidance for Validation:** These commands validate and build source without activation. Deployment, preparation, registration, package installation, and service operations affect live state and require that state to be within the user's task. **Do not run deployment or mutation commands to validate documentation.**
- **Documentation Standards:** For documentation-only edits, check Markdown syntax, relative links, and run `git diff --check`.
  - Keep [README.md](./README.md) as the entry point.
  - Keep [CONTEXT.md](CONTEXT.md) as the composition model.
  - Keep `docs/` limited to current operator procedures. Update the relevant documentation when public behavior changes, and keep agent constraints here instead of duplicating runbooks.
