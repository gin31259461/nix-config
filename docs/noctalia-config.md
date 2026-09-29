# Noctalia preferences

`noctalia-config` moves reviewed UI preferences between live Noctalia settings and the repository snapshot at `homes/abnertu/noctalia/config.toml`. Home Manager manages the corresponding home link. The tool does not own the encrypted storage key or application data; see [desktop session](desktop-session.md).

## Moonlit desktop

The reviewed snapshot declares `Pictures/Wallpapers/Noctalia/moonlight.png` as the default wallpaper, uses its dark palette, and arranges the top bar, a floating Control Center at the top right, notifications, and Media and Calendar desktop cards. Widget coordinates target the current `HDMI-A-1` output at 1920×1080 and scale 1. Reposition them in the source snapshot if the output or scale changes. The Media card remains visible without a player, but needs an active MPRIS player for artwork and track controls. The Calendar card shows a month grid and an empty event area until calendar event synchronization is configured separately.

The single snapshot remains the owner of Noctalia visual preferences. Its `wallpaper` section is eligible for reviewed capture and controlled deployment. GUI wallpaper selection writes an override that takes precedence over the declared default; `deploy --dry-run` detects conflicts, and the existing `--replace-overrides` procedure below clears only owned sections while Noctalia is stopped. Do not copy the downloaded plan's additional TOML files into the live config directory, where they would duplicate snapshot ownership.

The Hyprland palette template remains enabled for the local development worktree. Other Noctalia app templates are disabled here because Kitty, Ghostty, GTK and Qt configuration files are managed by Home Manager. Their checked-in terminal themes provide readable static colors; enabling a template requires a writable output path and an explicit ownership change. Noctalia's palette and terminal themes therefore need a visual check after wallpaper changes.

Validate source without reading live Noctalia state:

```bash
noctalia config validate homes/abnertu/noctalia/config.toml
```

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
