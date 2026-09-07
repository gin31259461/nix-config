# Configuration module development plan

## Intended contract

Use `configuration.nix` as the selected Host module. Import reviewed Host values
explicitly, declare typed options in their owning interfaces, and keep reusable
defaults separate from ordinary user definitions. Use the nixpkgs module system
for imports, merging, unknown-option errors and override priorities. Arch and
Home Manager remain the realization owners; this is not a NixOS installation.

All exposed optional capability switches default to true. Required identity,
login-account values, hardware intent and fixed security policy remain required
or constrained values. Empty Runner instances create nothing. Disabling a
capability withdraws desired contributions, without retiring existing state.

## Implementation sequence

1. Research official configuration/module documentation and nixpkgs source;
   record citations and identify the patterns that apply to Arch.
2. Introduce a typed evaluator and explicit root configuration; group identity,
   networking, internationalization, time, services, programs, virtualization,
   hardware, users and deployment. Preserve validation behind the adapter seam.
3. Separate defaults from Host overrides. Expose parent/child capability switches,
   user profile/module selection, native services and desktop applications.
   Propagate selections through package inventories, system units, home units,
   static files and optional flake outputs. Preserve startup dependencies.
4. Add isolated interface/composition checks for defaults, imports, priorities,
   invalid values, disabled capabilities and generated unit relationships.
5. Run focused checks, then all flake checks and public package/home builds.
   Stage exact source paths before flake evaluation. Never deploy for validation.
6. Rewrite README and agent instructions, update composition terminology and
   operator guides, and document the new entry point and disable semantics.
7. Review the staged diff, commit with a scoped Conventional Commit subject,
   and push the current branch to its configured remote.

## Acceptance criteria

- Ordinary definitions override defaults; imports and list merging work.
- Unknown options and invalid enabled declarations fail before deployment.
- Every exposed enable option defaults to true and accepts false.
- Disabled capabilities contribute no owned requirements, units or files;
  independent requirements (especially Runner Podman) remain selected.
- Native package/service ownership, UWSM/tray lifetimes, runtime secrets,
  repeat execution and failure recovery retain their existing invariants.
- Documentation points to executable inventories and preserves preparation and
  recovery instructions. No live state is inspected or changed for validation.

## Completion and validation

Implemented on 2026-09-07. The public entry uses typed namespaces and default-on
capabilities, with Host `mkDefault` values and a deferred Home Manager override
module. Adapter selection covers native services, desktop applications,
initramfs, repository queries and optional helper outputs. Independent fixtures
exercise all public enable switches, imports/list merging, invalid definitions,
individual Runner disabling, home overrides and a headless home build.

Passed:

- `nix build --no-link .#checks.x86_64-linux.source-format`
- `nix flake check`, including the isolated UFW coexistence VM
- Home Manager `abnertu@arch` activation package build
- `arch-switch` and `runnerctl` builds
- Local documentation links/fences and staged/working `git diff --check`

The custom `configurations` inspection output produces the documented
unknown-output warning. No deployment, package installation on the Host,
service changes, Runner operations or private application-state inspection was
performed. Native adoption prerequisites remain an operator decision before
activation. README and agent instructions were rewritten; configuration,
composition, deployment and recovery documentation now describe the public
entry and its default-on/disable behavior.
