# Vendored asset provenance

This repository deploys tracked configuration assets directly from `files/home/`.
Those files are part of the reviewed source boundary and must not become an
untraceable dependency channel.

## Current inventory

| Path | Provenance | Update policy |
| --- | --- | --- |
| `files/home/.agents/skills/` | Historical vendored skill set. Per-skill upstream revision and license were not recorded when these files entered the repository. | Treat current contents as repository-owned snapshots. Do not refresh or replace a skill until its upstream URL, revision/tag, license and review notes are recorded in the same change. |
| `files/home/.config/quickshell/` | Repository-maintained desktop configuration. | Review as first-party source; all tracked QML/JavaScript/JSON is syntax-checked before deployment. |
| `nvim-config` flake input | `gin31259461/nvim-config`, pinned by `flake.lock`. | Update through the flake lock so source revision and NAR hash remain reviewable. |
| `hypr-config` flake input | `Orbit-Lua/hypr`, pinned by `flake.lock`. | Update through the flake lock so source revision and NAR hash remain reviewable. |

The missing historical metadata for `.agents/skills` is explicitly documented
rather than guessed. Future imports must not repeat that gap.

## Required metadata for new vendored imports

Every newly vendored third-party subtree must add or update this document with:

- canonical upstream URL;
- exact revision, tag or release;
- upstream license and any attribution obligations;
- paths included/excluded from the import;
- integrity mechanism (normally a pinned flake input or reviewed Git commit);
- update procedure and any local patches.

Prefer a flake input when an asset changes independently and its upstream history
is useful. Keep assets vendored when they are intentionally curated, locally
patched or small enough that direct review is clearer than another dependency.

## Review rule

A vendor refresh is a source change, not a formatting change. Review the upstream
diff first, then the repository projection, then run the full flake checks. Never
replace a vendored directory from an unpinned network download during activation.
