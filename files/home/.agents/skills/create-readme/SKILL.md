---
name: create-readme
description: Create, rewrite, refresh, or audit a repository README from current source evidence while respecting the requested scope and established presentation.
---

# Create a repository README

Write a useful entry point for the project's users and developers. Explain
current behavior, the first useful workflow, configuration and validation.
Keep the repository's recognizable presentation unless the user requests a
different style or it obstructs those outcomes.

## Interpret the request

- Create: derive a suitable document when none exists.
- Rewrite: reassess the entire document and produce coherent current prose.
  Rewriting does not by itself require replacing headings, layout or visuals.
- Restructure or redesign: reorganize the document to serve the requested
  audience and workflow; retain useful content and assets.
- Refresh: correct and improve the requested material within the existing form.
- Restore style: recover the requested presentation while keeping current facts,
  commands and interfaces. Consult history as evidence, not as a whole-file
  rollback instruction.
- Audit: report evidence-backed findings without editing unless requested.

Explicit user preferences take precedence. Do not manufacture visible changes
just to prove that a rewrite occurred. A rewrite should be complete in substance,
but may keep an effective outline.

## Establish the evidence and presentation

Read applicable AGENTS instructions, Git status, the current README and relevant
companion documents. Inspect manifests, task runners, CI, configuration and CLI
source for the workflows being documented.

Before composing, identify:

- the audience, supported environment and shortest useful workflow;
- commands and interfaces that changed;
- the existing tone, heading depth, section order and table conventions;
- badges, preview images, screenshots, diagrams and useful navigation;
- obsolete statements, duplicated inventories and missing essential guidance.

Treat existing useful presentation as an asset. Preserve valid badges and public
preview images unless the user requests removal or evidence shows they are
obsolete, broken, redundant or inappropriate. Verify asset paths; do not silently
remove an image reference while leaving its useful asset behind.

For a new README, choose a compact presentation from project evidence. Add badges
or visuals when they communicate useful verified information, not to satisfy a
fixed template. Link badges to relevant authoritative pages.

## Compose current documentation

Choose sections that help the reader use and maintain this particular project.
Use compact factual paragraphs, runnable examples and tables for useful mappings.
Keep the project name, terminology and established style consistent.

Preserve verified facts and useful examples. Replace stale commands with their
current equivalents. Distinguish declared configuration, built artifacts and
actual runtime state when the difference matters. Describe planned work only as
planned; passing existing tests does not establish that an entire refactor is
implemented.

Use executable policy as the authority for inventories. Do not claim a metadata
file controls dependency versions unless the build actually consumes it. Keep
credentials and sensitive machine data out of examples.

Respect companion ownership:

| Document | Content |
| --- | --- |
| README.md | Purpose, first use, public workflows and development entry |
| AGENTS.md | Agent ownership, editing constraints and validation rules |
| Architecture/domain document | Composition and operational relationships |
| Operator runbooks | Detailed procedures and recovery |

Link to existing companions instead of copying them. Do not create additional
documents or migration narratives merely to complete a template. Follow the
repository's rules for retaining only current documentation.

## Validate and hand off

Verify commands against their definitions and check links, image targets, code
fences and tables. Run available Markdown checks and git diff --check as
appropriate. Do not activate, deploy, register, install system packages or clean
application data to validate prose.

Compare the final document with the original: account for removed visuals,
badges, sections and substantive facts. Confirm that intended content changes
are present and stylistic restoration has not reverted working commands or
current behavior.

Summarize what changed and what was validated. Mention deliberate removal of
significant presentation assets or unresolved factual claims. Commit or push
only within the user's authorized workflow.
