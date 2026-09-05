# Desktop session and password store

UWSM owns session startup. KeePassXC loads its database minimized at login,
without a password; unlock it through the GUI when an application needs a
secret. Noctalia starts independently and uses a separate file-backed storage
key. Tray consumers follow Noctalia; Vicinae permits degraded startup after a
bounded ten-second tray wait. Remmina's background applet remains disabled here.

## Ownership and security

The Host selects `keepassxc` and `noctalia-storage` separately.
`modules/home/keepassxc.nix` owns password-free process startup;
`homes/abnertu/home.nix` supplies the runtime database filename:
`/home/abnertu/.local/share/keepassxc/credentials.kdbx`.
There is no credential delivery, automatic restart, unlocked-collection probe
or tray-repair restart. Existing KeePassXC GUI settings and database protection
are not modified. The old `keepassxc-password.cred` remains unused and untouched.

`modules/home/noctalia-storage.nix` owns `~/.config/noctalia/storage.toml` and
the guarded first-activation transition. It selects `storage.key_source = "file"`
and disables calendar synchronization. The guard rejects configured calendar
accounts, conflicting storage overrides and config includes pending review.
It does not silently rewrite GUI settings or account credentials.

The key lives at `~/.local/share/noctalia/file-key-v1/master-key`, with directory
mode `0700` and file mode `0600`. Activation generates 32 random bytes encoded
as 64 lowercase hexadecimal characters. Only the filename enters Nix artifacts.
Neither key contents nor encrypted data are imported into Git or the Nix store.
This key is unrelated to KeePassXC's password or database key file.

Noctalia data remains encrypted, but any process able to read both this key and
the encrypted files can decrypt it. KeePassXC's locked state no longer protects
Noctalia history. Back up the new key securely alongside any data you need to
recover; losing it cannot be repaired by generating another key.

## First activation: pause Noctalia, not Hyprland

Keep a terminal open in Hyprland. Pause only Noctalia, then run deployment from
the repository. The bar and launcher will temporarily disappear; existing
application windows remain open. A text console is an alternative, not a requirement.

```bash
systemctl --user stop noctalia.service
nix run .#arch-workstation && systemctl --user start noctalia.service
```

First activation refuses to proceed if Noctalia is running. It does not stop
services itself. Do not launch Noctalia or tray consumers that pull it in
concurrently with this transition. If activation fails after migration starts,
finish recovery before restarting Noctalia.
The transition uses the Home Manager XDG paths; the following are this Host's
defaults:

| Existing data | Preserved location |
| --- | --- |
| `~/.local/state/noctalia/clipboard` | `~/.local/state/noctalia/clipboard.before-file-key` |
| `~/.cache/noctalia/calendar` | `~/.cache/noctalia/calendar.before-file-key` |

Existing directories are renamed, never decrypted, overwritten or deleted.
Noctalia starts with fresh history/cache under the original directory names.
Its GUI settings, other UI state and old Secret Service key remain untouched.
Archived data still needs its original key for recovery; the new key cannot
decrypt it. Archive destinations must not already exist before the transition.

A persistent lock protects the transition. A `pending` marker is written before
renames and key creation; `ready` marks completion. Interrupted transitions can
resume without replacing a published key. Repeat activation preserves the key,
its timestamp and new application data; it does not create repeated archives.
Home Manager dry-run validation never generates a key or moves data.

## Recovery and configuration conflicts

- If Noctalia is running during first activation, stop its user service and retry.
- An existing `~/.local/share/noctalia/storage-key` may be a key file, not a
  directory. It remains untouched; the new transition uses `file-key-v1/` to
  avoid that collision. Never delete or overwrite an unknown existing key.
- If a conflicting `[storage]` override or calendar account is reported, review
  the relevant `~/.config/noctalia/*.toml` and GUI-managed
  `~/.local/state/noctalia/settings.toml` locally. Remove only the conflicting
  setting after deciding its intended behavior; never publish the entire file.
- Included config or custom `NOCTALIA_*_HOME` roots require a separate review;
  the transition refuses to guess which data belongs to them.
- If an archive collision or symlink is reported, preserve both locations and
  resolve ownership manually. Do not delete archives to make activation pass.
- If migration was interrupted, keep `pending`, the lock inode and any published
  key in place, stop Noctalia, and rerun deployment.
- If `ready` exists but the key is missing, restore the exact key from a secure
  backup. Do not remove `ready` to force key regeneration.
- Incorrect key-state ownership or permissions must be fixed deliberately;
  expected directory/file modes are `0700`/`0600` for the login user.

Rolling back a Home Manager generation does not reverse a data transition.
Restoring archived history requires an offline, separately reviewed restoration
of its matching old key and configuration, while preserving any new history.

## Why file mode matters

The inspected Noctalia build (`e9230c81b`) configures encrypted storage even with
clipboard history disabled. In Secret Service mode, its
[lookup](https://github.com/noctalia-dev/noctalia/blob/e9230c81b/src/security/secret_store.cpp)
requests unlocking. The
[file-key implementation](https://github.com/noctalia-dev/noctalia/blob/e9230c81b/src/security/storage_key_provider.cpp)
instead reads the configured key file. Calendar credentials are a separate
Secret Service consumer, hence the account guard.

File mode is not a global D-Bus ban: Noctalia still has an availability probe
that opens a Secret Service session, without the lookup's unlock flag. Other
applications, plugins or later GUI changes can still request secrets and cause
a prompt. The managed policy removes the identified storage-key unlock request;
it cannot classify all future requests as background versus user initiated.

## Verify after logging in

```bash
systemctl --user is-active noctalia.service keepassxc.service
systemctl --user show noctalia.service -p Wants -p Requires -p After
```

Expect both services active, no KeePassXC dependency on Noctalia's unit, and a
locked database without an unsolicited unlock prompt. Check the tray and launcher,
then deliberately use an application requiring Secret Service and enter the
password in KeePassXC. Closing KeePassXC must not stop Noctalia. Starting an
already active unit must not restart it; use the tray/window to raise it.

These are operator acceptance checks, not claims made by source builds. If a
prompt still appears at login, investigate other startup consumers without
dumping INI files, credentials or D-Bus secret payloads.

```bash
nix build --no-link .#checks.x86_64-linux.noctalia-storage
nix build --no-link .#checks.x86_64-linux.graphical-session-ordering
nix flake check
```

The migration tests run only against temporary fixtures and fake process state.
