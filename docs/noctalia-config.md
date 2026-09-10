# Noctalia configuration

`noctalia-config` exchanges reviewed Noctalia UI preferences between live user
settings and the repository snapshot. It does not own encrypted storage keys or
application data.

The reviewed snapshot is stored at:

```text
homes/abnertu/noctalia/config.toml
```

Home Manager owns the corresponding managed config link.

## Capture

Run from the repository checkout:

```bash
nix run .#noctalia-config -- capture --dry-run
nix run .#noctalia-config -- capture
```

Capture exports the effective Noctalia settings, filters them to the owned UI
sections, validates a temporary candidate and atomically updates the repository
snapshot only when needed. It does not stage, commit or push changes.

Review the resulting Git diff before committing. User labels, paths and other UI
values can still be private even when they are within the supported filter.

Validation warnings stop capture. Inspect detailed live validation locally when
needed:

```bash
/usr/bin/noctalia config validate
```

## Deploy preferences

```bash
nix run .#noctalia-config -- deploy --dry-run
nix run .#noctalia-config -- deploy
```

Deploy builds and activates the complete selected Home Manager configuration and
then verifies the managed Noctalia sections. It does not run Arch convergence.
The built Home Manager generation is fixed before activation.

If live GUI overrides conflict with repository-owned sections, deployment stops.
To deliberately replace those owned override sections:

```bash
systemctl --user stop noctalia.service
nix run .#noctalia-config -- deploy --replace-overrides
systemctl --user start noctalia.service
```

The replacement flow preserves unowned sections and writes private recovery state
before changing overrides. The command does not stop Noctalia automatically.

## Recover

Recovery state is stored under:

```text
~/.local/state/nix-config/noctalia-config/
```

If an override replacement is interrupted, keep the receipt and backup intact,
stop Noctalia and run:

```bash
nix run .#noctalia-config -- deploy --recover
```

Recovery restores saved bytes only when the current state still matches the
recorded transition. Concurrent edits require manual reconciliation.

Noctalia encrypted-storage initialization is a separate Home Manager capability;
see [desktop session](desktop-session.md).

## Validate source

```bash
nix build --no-link --show-trace --print-build-logs \
  .#checks.x86_64-linux.noctalia-config .#noctalia-config
just check
```

Tests use temporary homes and fake commands. They do not inspect live settings,
activate the real home or restart services.
