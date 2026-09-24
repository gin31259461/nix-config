---
name: create-agentsmd
description: Create, rewrite, refresh, or audit repository and scoped AGENTS.md files. Derive actionable ownership, editing and validation rules from project evidence while preserving valid policy and keeping instructions concise.
---

# Create AGENTS instructions

Write the project-specific guidance that helps an agent make correct changes.
The document should answer where to edit, which contracts to preserve, how to
validate, and which actions need different scope. Keep each instruction useful
enough to justify loading it on future tasks.

## Match intent and ownership

Create missing instructions; rewrite by reassessing the complete contract;
refresh only the requested area for a focused update. Audit reports findings
without editing unless authorized. Preserve the user's language, style and
scope. A rewrite need not change effective headings or layout. Restore style
from history without restoring stale commands or deleting newer valid policy.

Find the owning source before editing symlinked, generated or centrally managed
files. Do not expand a repository task into global agent settings, other tools'
configuration, implementation work or deployment. Do not create compatibility
symlinks or new scoped files merely because another project uses them.

For a new file, a substantial rewrite, or conflicts between scopes, read
[rule design and scope](references/rule-design-and-scope.md). It provides examples,
tool-specific discovery considerations and behavioral review scenarios.

## Gather rules from evidence

Read Git status, applicable parent and scoped instructions, the README, relevant
architecture documents, manifests, task definitions, CI and representative tests.
Find ownership boundaries, generated files, external source trees and protected
runtime paths. Inspect only what is needed; never read secret or mutable data
to document how it should be protected.

For a rewrite, keep a working inventory of the existing material rules and their
disposition: retain, clarify, relocate or remove with a reason. This is a review
aid, not a new repository document. Distinguish the following evidence:

| Evidence | How to use it |
| --- | --- |
| Explicit user or repository policy | Preserve as policy even when current implementation violates it; report discrepancies |
| Current implementation and executable configuration | Establish actual paths, interfaces, command behavior and ownership |
| Repeated local conventions | Describe at the narrowest justified scope; do not invent universal mandates |
| Proposed design or historical workaround | Do not present as implemented or mandatory without current authority |

Investigate an unclear rule before deleting it. Documentation may describe an
intentional invariant that is not yet enforced. Conversely, one unusual source
file is not enough to mandate a new repository-wide style.

## Put guidance at the scope that needs it

Keep repository-wide boundaries and common workflows at the root. Put meaningful
package-specific exceptions close to their files when nested instructions are
within the task. Avoid copying all parent rules into every child or generating
one AGENTS.md per directory by default.

Read the target tool's actual instruction chain when tool-specific discovery
matters. Do not assume all tools automatically load every nested file, use the
same override filenames, or reread changed instructions mid-session. Critical
guidance should be discoverable from the relevant entry point. If child files
need explicit routing, link them with a clear "read before editing" condition.

Reconcile conflicting scopes instead of leaving contradictory commands in place.
Do not silently weaken a valid parent contract. Respect user authority and existing
authorization; avoid introducing blanket confirmation requirements for ordinary
reversible edits. A documentation change does not itself authorize new live
operations or change the current session's permissions.

## Write rules that change decisions

For each candidate instruction, ask: would a capable agent plausibly make a
different, worse choice without it? If not, omit it, link its owning reference,
or leave it to existing tooling.

Prefer a concrete action, its scope, and a short reason when the reason prevents
misapplication. Include a condition or exception when needed. Say where the agent
should edit and how to validate, not merely what to avoid. Keep related rules
together and use "must" or "never" only for real constraints.

Select only evidence-supported categories:

- Ownership: the authoritative configuration, schema, generator or module for
  each kind of change; real boundaries between packages or layers.
- Change contracts: public interfaces, compatibility, defaults and overrides,
  generated-source rules, migrations and domain invariants.
- Workflows: required setup, useful entry points and exact validation commands
  with their working directory, prerequisites and applicability.
- Side effects: preparation, deployment, registration, failure handling and
  recovery responsibilities when they are part of this repository.
- Protected state: paths or classes of data that must stay unread, unlogged,
  outside version control or outside generated artifacts.
- Documentation: which public or architectural changes require updates, and
  which document owns each kind of information.

Preserve precise failure and lifecycle qualifications: optional skip conditions,
partial diagnostics, secret redaction, disabled-state semantics, retention,
pending markers and required validation. Do not compress these into vague advice
such as "handle failures safely". Keep critical constraints self-contained;
links may supply context but must not hide the operative rule.

## Make validation actionable and proportional

Check command definitions and their transitive scripts before recommending them.
Record the required context: working directory, setup, command, what it checks,
and whether it writes files or changes live systems. Distinguish check-only
commands from auto-fix, snapshot-update, regeneration and deployment commands.

Use the repository's actual fast, focused and full-check paths. State which
changes require which checks where policy provides that distinction. Preserve
mandatory checks; do not invent a test matrix or a universal full-suite rule.
For documentation-only changes, keep verification to documentation unless an
applicable repository rule explicitly requires more.

Prefer behavior and public-contract tests over assertions that copy production
inventories or freeze private implementation details. Where side effects are
involved, point to existing synthetic fixtures, fake adapters or isolated VMs.
Do not invent successful checks or normalize a real failure into a skip.

## Keep the document compact and maintainable

Use the established title or `# AGENTS Instructions`. Group by decisions an agent
makes: ownership, change constraints, validation and relevant operational limits.
Use command blocks and small tables when useful. There is no required set of
headings or line-count target; shorten duplication before removing meaning.

Exclude promotional prose, badges, generic coding lectures, ephemeral status,
large directory listings and instructions already enforced by the formatter.
Keep package, service and account inventories in their owning source. Reference
that owner instead of reproducing values that drift. Avoid imposing incidental
production constants or private implementation shape on future tests.

README introduces the project; architecture documents explain composition;
runbooks describe operator procedures; AGENTS governs changes. Link them with
a purpose and a relevant trigger. Do not create history documents, runbooks or
new policy just to fill an instruction template.

## Review the resulting decisions

Check every path and command. Read root and affected child instructions together
for contradictions, missing routes and duplicated rules. Compare the finished
file with the original inventory: each material contract must survive or have
an evidence-backed reason for deliberate removal.

Walk through representative tasks: a documentation edit, a normal code change,
an edit to generated output, a cross-package change, and a task near protected
or live state when applicable. The instructions should lead to the correct owner,
checks and scope without unnecessary approvals or unrelated work.

Use available Markdown checks, relative-link checks and `git diff --check`.
Validate documentation without live deployment, activation, registration,
package installation or data cleanup. Read README and AGENTS together to catch
contradictory public workflows while preserving their separate responsibilities.

Report the edited scopes, meaningful rule changes and validation. Flag unresolved
policy/implementation discrepancies accurately. Writing an intended contract
does not implement it. Commit or push only within the authorized workflow.
