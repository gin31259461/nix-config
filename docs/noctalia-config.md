# Noctalia preferences

`noctalia-config` moves reviewed UI preferences between live Noctalia settings and the repository snapshot at `homes/abnertu/noctalia/config.toml`. Home Manager manages the corresponding home link. The tool does not own the encrypted storage key or application data; see [desktop session](desktop-session.md).

## Capture a reviewed snapshot

Run from this checkout:

```bash
nix run .#noctalia-config -- capture --dry-run
nix run .#noctalia-config -- capture
```

Capture exports effective settings, filters to owned UI sections, validates a temporary candidate and atomically updates the snapshot only when content differs. It does not stage, commit or push. Review the Git diff before committing: user labels, paths and other supported UI values may still be private. Validation warnings stop capture. To inspect live validation locally, run `/usr/bin/noctalia config validate`; keep its output private if it contains personal values.

## Deploy preferences

```bash
nix run .#noctalia-config -- deploy --dry-run
nix run .#noctalia-config -- deploy
```

Deploy builds and activates the selected Home Manager configuration, then verifies managed Noctalia sections. It does not run Arch convergence. The generation is fixed before activation. Conflicting live GUI overrides stop deployment. To deliberately replace owned override sections, stop Noctalia first:

```bash
systemctl --user stop noctalia.service
nix run .#noctalia-config -- deploy --replace-overrides
systemctl --user start noctalia.service
```

Unowned sections remain untouched. The tool writes private recovery state before changing overrides; it does not stop the service automatically.

## Recover and validate

Recovery state lives under `~/.local/state/nix-config/noctalia-config/`. After an interrupted replacement, keep the receipt and backup, stop Noctalia and run:

```bash
nix run .#noctalia-config -- deploy --recover
```

Recovery restores saved bytes only if current state still matches the recorded transition. Concurrent edits require manual reconciliation. Source-only tests use temporary homes and fake commands:

```bash
nix build --no-link --show-trace --print-build-logs \
  .#checks.x86_64-linux.noctalia-config .#noctalia-config
just check
```
