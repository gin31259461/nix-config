---
name: create-agentsmd
description: Create, rewrite, refresh, or audit scoped AGENTS.md instructions from repository evidence, preserving valid constraints and the user's requested style.
---

# Create AGENTS instructions

Write a compact operational contract containing rules that change an agent's
decisions. Preserve valid project-specific constraints and the repository's
established instruction style.

## Interpret scope and intent

Create instructions when missing. Rewrite by reassessing the full instruction
set and composing a coherent current document; the word "rewrite" does not
require new headings or a different layout. Restructure when requested or when
the existing organization hides important constraints. Refresh focused material
for narrower requests. Audit without editing unless changes are authorized.

When restoring style, use prior versions to recover tone and organization while
retaining current contracts. Do not restore historical files wholesale and
thereby remove valid new rules or bring back retired commands.

Follow explicit user preferences. Do not expand a documentation task into
implementation, deployment or changes to unrelated agent configuration.

## Read the owning evidence

Read applicable parent and scoped AGENTS files, Git status, README, composition
documents and relevant build, configuration, CI and test source. Identify
generated, sensitive and externally owned paths.

For each important existing instruction, determine whether to retain, clarify,
move or remove it. Distinguish:

- explicit user or repository policy, which source behavior may currently violate;
- implementation facts supported by current code;
- proposed design choices that have not been implemented.

Do not weaken a valid requirement because the code violates it. Report the
discrepancy. Do not promote a preference or proposed abstraction into a universal
constraint. If a rule's purpose is unclear, investigate before removing it.

Create nested instructions only where ownership, safety or workflows materially
differ and the task covers that scope. Avoid duplicating parent rules.

## Preserve a useful instruction style

Keep effective headings, ownership tables, command blocks, terminology and
imperative tone. Reorganize when there is a concrete readability or scope reason.
Use the established title, or "# AGENTS Instructions" for a new document.

Be concise without deleting operational meaning. In particular, preserve
qualifications and exceptions around optional skips, diagnostics, secrets,
disabled-state behavior, data retention and required validation when those
contracts exist in the repository.

Keep agent constraints self-contained. Link to architecture and runbooks for
background; do not replace a critical rule with a vague link.

## Write actionable constraints

Include only categories justified by evidence:

- ownership of configuration, packages, files, accounts and services;
- public interface validation, defaults and override semantics;
- generated sources, runtime data and external source ownership;
- side effects, explicit preparation and failure handling;
- protected data and non-logging requirements;
- meaningful testing contracts and exact validation commands;
- documentation obligations when public behavior changes.

Explain which commands are source validation and which affect live systems.
Use isolated fixtures or fake commands for testing side effects where available.
Respect authorization already supplied by the user; avoid blanket approval
requirements for ordinary reversible edits.

Keep authoritative inventories in source. State their owner rather than
duplicating every package or service. Do not turn incidental production values
or private implementation shape into mandatory test assertions.

Separate responsibilities: README introduces the project, runbooks describe
operator procedures, composition documents explain architecture, and AGENTS
governs changes. Do not create historical narratives or new companion files
unless the repository and task require them.

## Verify completeness and correctness

Check every path and command against source. Reconcile parent and nested rules.
Review the finished instructions against the original constraint inventory:
each material rule must survive, be deliberately clarified or have an
evidence-backed reason for removal. Preserve stronger user policy even when
implementation work remains.

Run applicable Markdown checks and git diff --check. Validate prose without live
deployment, registration, package installation or cleanup. Read README and
AGENTS together to catch contradictions while keeping their roles distinct.

Report changed scope, important retained or revised constraints and validation.
Do not claim implementation work was completed merely because instructions now
describe the intended design. Commit or push only within authorized scope.
