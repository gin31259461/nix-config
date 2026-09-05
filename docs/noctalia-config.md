# Capture and deploy Noctalia v5 preferences

Run from this repository's root. Before the command is installed in the home
profile, use `nix run .#noctalia-config --` in place of `noctalia-config`.
Use `--repo /absolute/path/to/nix` when running outside the checkout.

```bash
noctalia-config capture --dry-run
noctalia-config capture

noctalia-config deploy --dry-run
noctalia-config deploy
```

`capture` writes reviewed-scope preferences to
`homes/abnertu/noctalia/config.toml`. `deploy` builds and activates the **complete
selected Home Manager configuration**, not only Noctalia. It never runs Arch
package convergence. Neither operation stages, commits or pushes Git changes.

## What v5 stores where

The [official v5 configuration model](https://docs.noctalia.dev/noctalia/configuration/)
has three distinct files/owners:

| Location (default) | Owner and meaning |
| --- | --- |
| `~/.config/noctalia/*.toml` | Handwritten configuration, including Home Manager links |
| `~/.local/state/noctalia/settings.toml` | Writable GUI overrides; loaded after handwritten configuration |
| `~/.local/state/noctalia/state.toml` | Internal runtime state; never synchronized by this command |

Capture uses `/usr/bin/noctalia config export`, which merges user settings without
materializing all built-in defaults. It does not copy the GUI file verbatim or
use `export full`. Noctalia resolves its `NOCTALIA_CONFIG_HOME` and
`NOCTALIA_STATE_HOME` overrides before the corresponding XDG roots. Capture
honors those paths. Deployment currently requires this Host's default XDG roots;
it rejects alternate roots until Home Manager ownership is configured for them.

## Capture scope and review

The Module explicitly permits selected UI sections: theme, bar, widget, dock,
desktop, shell, OSD, notification, audio, brightness, battery, control center,
accessibility and night light. A section containing nonempty fields whose names
indicate commands, actions, scripts, URLs, keybindings, accounts or credentials
is omitted as a whole for review. Unsupported/new sections are also omitted.
Only section names, never values or a raw exported diff, appear in command output.

This is a conservative preference exporter, not a complete configuration backup
or a proof that arbitrary text is non-sensitive. Inspect the captured diff
locally before committing, especially labels, custom text and filesystem paths.
Do not broaden the allowlist to import secrets or executable settings implicitly.
Storage and calendar policy stay in `noctalia-storage.nix`; key files, clipboard
data, event caches and internal state are never exported.

The checked-in preferences file starts empty. No live GUI settings are captured
by builds or automatically when installing this command. Capture validates a
private temporary candidate first, refuses validation warnings, and atomically
writes the tracked file only if its content/metadata differs. Concurrent edits
to the repository file cause capture to stop. It does not rewrite GUI overrides.

## Deployment and GUI conflicts

Home Manager remains the sole owner of `~/.config/noctalia/config.toml`.
The command refuses an unmanaged file at that path and competing handwritten
TOMLs that own the same sections; it never overwrites them itself.

The repository owns each preference section it contains as a whole. GUI overrides
that change or add values in those sections are conflicts. Default deployment
reports their section names and stops before building or changing overrides.
Overrides with identical values are harmless and can remain.

To explicitly replace overrides for repository-owned sections:

```bash
# Keep a terminal open; existing Hyprland application windows remain usable.
systemctl --user stop noctalia.service
noctalia-config deploy --replace-overrides && systemctl --user start noctalia.service
```

The command does not stop/restart services on your behalf. Replacement requires
Noctalia to be stopped, builds the home first, then writes a private backup and
a pending receipt before removing owned sections from the GUI override file.
Unowned sections remain. The backup lives under
`~/.local/state/nix-config/noctalia-config/` (directory `0700`, backups `0600`).
It is not adjacent to a Home Manager link and is never committed or imported
into the Nix store. No automatic backup cleanup is performed.

After Home Manager activation, the command exports the effective user config
again and compares the managed sections with the repository. This detects a
successful file deployment that did not actually take precedence. Unchanged
override content does not create additional backups on repeat invocation.

Dry runs validate and report section names using temporary files only: no home
build/activation, persistent lock, backup, override edit or repository write.
They do inspect live configuration and should not be used as CI/source tests.

## Failure recovery

A failed activation or effective-config comparison restores changed GUI overrides
when they still match the command's written version. It does **not** roll back
the Home Manager generation or other home changes. Backups remain available.

For an interrupted deployment:

```bash
systemctl --user stop noctalia.service
noctalia-config deploy --recover
```

Recovery restores the exact backed-up overrides only when the current file
matches the before/after receipt hash. Concurrent GUI/manual edits cause recovery
to stop rather than overwrite them. Preserve the backup and receipt for manual
reconciliation. A pending receipt blocks further capture/deploy until recovery.
Do not delete the persistent lock inode.

Once recovery succeeds, review the repository and retry deployment. Start
Noctalia only after resolving any storage migration failure as described in
[desktop-session.md](desktop-session.md). Pausing Noctalia is sufficient; logging
out of Hyprland is not required.

## Source validation

```bash
nix build --no-link .#checks.x86_64-linux.noctalia-config
nix build --no-link .#noctalia-config
nix flake check
```

Tests use temporary repositories/homes and fake native, Git and Nix commands.
They do not export the machine's settings, activate Home Manager or restart services.
