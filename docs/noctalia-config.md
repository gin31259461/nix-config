# Noctalia preference exchange

`noctalia-config` captures reviewed UI preferences into Git and deploys them
through Home Manager. Run from `~/.config/nix`, or pass `--repo` with the absolute
checkout path. Use `nix run .#noctalia-config --` to run the current source without
first installing the command.

## Capture current preferences

```bash
nix run .#noctalia-config -- capture --dry-run
nix run .#noctalia-config -- capture
```

The destination is
[homes/abnertu/noctalia/config.toml](../homes/abnertu/noctalia/config.toml), or
`~/.config/nix/homes/abnertu/noctalia/config.toml` in the normal checkout.
Capture exports merged user settings, filters their scope, validates a private
temporary candidate, and atomically replaces the snapshot only when needed.
It leaves GUI overrides unchanged and never stages, commits or pushes.
Diagnostics list only fixed, known section names; unsupported sections are
reported by count to avoid exposing user-defined names.

Inspect the captured diff locally before committing. Labels, custom text and
paths can be private even when their fields pass the filter. Concurrent changes
to the repository snapshot cause capture to stop rather than overwrite them.

## Configuration ownership

| Location | Owner |
| --- | --- |
| `homes/<user>/noctalia/config.toml` | Reviewed repository preferences |
| `~/.config/noctalia/config.toml` | Home Manager link to the built snapshot |
| Other `~/.config/noctalia/*.toml` files | Their existing configuration owners |
| `~/.local/state/noctalia/settings.toml` | GUI overrides, loaded after configuration files |
| Runtime state, encrypted data and keys | Noctalia and the local storage policy |

The [capture filter](../modules/home/noctalia-config/sync.py) owns the allowlist
of UI sections. Unknown sections and whole sections containing nonempty
command, action, URL, account or credential-like fields are excluded for review.
Storage and calendar policy belong to
[noctalia-storage.nix](../modules/home/noctalia-storage.nix). Wallpaper selection,
plugin settings, internal state and encrypted data are outside capture scope.

Capture uses `noctalia config export`, not `export full` or a wholesale GUI-file
copy. It honors Noctalia/XDG config and state roots; deploy requires this Host's
default roots. Builds never capture live preferences automatically.

## Resolve validation warnings

Warnings stop capture before the snapshot is written. The error reports known
affected sections, such as `sections: widget`, and withholds raw diagnostics
because they can quote private values. Inspect full live warnings locally:

```bash
/usr/bin/noctalia config validate
```

The full live configuration and filtered candidate can have different warnings.
A widget referencing a disabled plugin can be unrecognized even when its files
are installed. Decide whether to enable that plugin or remove the stale widget
and its bar references. Capture does not make that decision automatically.
Editing only the repository snapshot leaves the live overrides intact, so a
subsequent capture can encounter the same warning until those are resolved.

## Apply the snapshot

```bash
nix run .#noctalia-config -- deploy --dry-run
nix run .#noctalia-config -- deploy
```

Deploy builds and activates the **complete selected Home Manager configuration**,
then verifies the effective managed sections. It does not run Arch convergence.
The build creates a temporary GC root outside the repository and activation
uses that exact generation, with Home Manager managing the generation profile.
Changes to other source files during the build cannot select a different
activation artifact. The temporary root is removed after the operation.
Home Manager alone owns the config link; deployment refuses unmanaged files,
competing TOML section owners and unreviewed includes.

GUI overrides differing from repository-owned sections are reported as conflicts.
Identical overrides can remain. To replace conflicting overrides deliberately:

```bash
systemctl --user stop noctalia.service
nix run .#noctalia-config -- deploy --replace-overrides && \
  systemctl --user start noctalia.service
```

Keep a terminal open. This stops the panel and its coupled launcher; other
application windows remain usable. The command itself never stops services.
Replacement builds the home first, records a private backup and pending receipt,
then clears only repository-owned override sections. It preserves unowned sections.
A subsequent build or activation does not silently clear overrides.

Dry-run capture/deploy inspect live settings but do not build or activate the
home, write the snapshot, change overrides, or create persistent recovery state.
They are operator previews, not source-validation tests.

## Recover an interrupted deployment

Recovery state lives under `~/.local/state/nix-config/noctalia-config/` with
directory mode `0700` and backup mode `0600`. Retain receipts and the persistent
lock inode; do not copy this directory into Git or remove backups automatically.

An ordinary activation or effective-config failure attempts to restore changed
GUI overrides. Timeouts preserve the pending receipt for explicit recovery.
Queries have a 30-second limit; building and activation each allow one hour.
On timeout the command's process group is killed before the tool releases its
lock. If termination is uncertain, inspect the interrupted operation before
recovery. Home Manager generations and other home changes are not rolled back.
For an interrupted operation:

```bash
systemctl --user stop noctalia.service
nix run .#noctalia-config -- deploy --recover
```

Recovery restores the saved bytes only when current settings match the receipt's
before/after hashes. Concurrent GUI or manual edits require deliberate
reconciliation. A pending receipt blocks further capture/deploy until recovery.
Once resolved, review the snapshot, retry deployment and restart Noctalia.
For missing keys or storage preparation failures, use the
[desktop storage recovery guide](desktop-session.md#recover-storage-safely).

## Validate changes to the tool

```bash
nix build --no-link .#checks.x86_64-linux.noctalia-config .#noctalia-config
nix flake check
```

Tests use temporary homes and fake native/Nix commands. They do not read live
settings, activate Home Manager or restart services.
