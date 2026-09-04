---
name: create-readme
description: Create, rewrite, restructure, refresh, or audit a repository README.md as concise, evidence-backed documentation for users and developers. When the user explicitly asks to rewrite, regenerate, rebuild, or restructure a README, rebuild the document as a coherent new README from repository evidence instead of merely polishing or preserving the existing README structure.
---

# Create a repository README

Produce a concise entry point that explains the project's current purpose,
first successful workflow, public interface, and relevant development path.
Derive every claim from repository evidence.

## Determine the requested mode

Classify the task before editing. The user's explicit wording controls the mode.

- **Create**: no useful README exists. Build one from repository evidence.
- **Rewrite**: the user says `rewrite`, `regenerate`, `rebuild`, `restructure`, or
  otherwise explicitly asks for a substantial replacement. Recompose the README
  as a new document. Preserve verified facts, not the old document's wording,
  headings, ordering, or layout.
- **Refresh**: the user asks to update, improve, clean up, or modernize the README
  without explicitly requesting a rewrite. Preserve useful structure when it
  still serves the reader, but fix stale or weak content.
- **Audit**: inspect and report issues without changing the README unless the user
  also asks for edits.

When the task is in **Rewrite** mode, do not reduce it to a sequence of local
edits. Build a target outline from this skill and current repository evidence,
then replace the README body with a coherent document that follows that outline.
The existing README is an information source, not the structural template.

Do not keep an existing heading, section order, paragraph, example, or layout
merely because it already exists. Keep it only when current evidence and the
reader's needs independently justify it.

## Discover the project

1. Read every applicable `AGENTS.md` before editing.
2. Inspect the existing README and nearby domain or migration documentation.
3. Inspect manifests, build files, task runners, CI, CLI usage, configuration
   schemas, tests, and executable scripts relevant to documented workflows.
4. Check Git status and preserve unrelated changes.
5. Classify the repository by its actual role, such as CLI, library,
   application, infrastructure, dotfiles, internal tool, or monorepo.
6. Identify the intended readers and the shortest path to a useful result.
7. In **Rewrite** mode, derive the target README outline from repository evidence
   and this skill before reusing any existing section structure.

Prefer executable source and current configuration over historical prose. When
documents conflict, resolve the claim from source or report the uncertainty;
do not guess.

## Set the documentation boundary

Keep each document responsible for one kind of information:

| Document | Responsibility |
| --- | --- |
| `README.md` | User/developer entry point and current public behavior |
| `AGENTS.md` | Coding-agent ownership, safety, editing, and validation rules |
| Domain documentation | Architecture and operational relationships |
| Migration guide | A version-bounded transition that is not yet complete |
| Source/config/scripts | Authoritative inventories and executable policy |

Allow only small, purposeful overlap: project identity, the most important
commands, a short ownership summary, and critical user-facing warnings. Link to
an existing companion document instead of copying its complete content.

Do not create additional documentation merely to satisfy this model unless the
user requested it or the repository clearly needs the split.

## Preserve current truth

- Preserve accurate, project-specific facts from an existing README.
- In **Rewrite** mode, preserve facts rather than prose or placement. Rewrite
  accurate material as needed so the final README reads as one intentionally
  designed document.
- Remove retired workflows, stale examples, duplicated inventories, and
  implementation history that no longer helps the reader.
- Document the system as it works now. Put unfinished transitions in a
  versioned migration guide rather than the main README.
- Use real command names, flags, paths, package/group keys, and configuration
  fields found in the repository.
- Point to an authoritative source for changing inventories instead of
  maintaining another hand-written list.
- Describe ownership and architecture at the level needed to use or develop the
  project; leave coding-agent guardrails to `AGENTS.md`.

## Choose sections from evidence

Use the project name as the top-level heading. Select only sections that serve
the identified readers. Common candidates include:

- a compact badge row with useful verified facts;
- a one-paragraph outcome and ownership summary;
- supported environments when support is intentionally bounded;
- installation or first-run instructions;
- task-oriented usage with a few verified examples;
- public configuration and its source of truth;
- a compact architecture or ownership explanation;
- development and validation commands; and
- troubleshooting for established, actionable failure modes.

Omit empty, speculative, or inapplicable sections. Do not force deployment,
database, API, coverage, pull-request, or troubleshooting content into every
project.

In **Rewrite** mode, choose the final section set and ordering from current
reader needs and repository evidence. Do not use the old README's outline as the
default starting point.

## Write in the Homebase style

- Lead with outcomes, then provide the shortest verified path to use them.
- Use plain, factual language and compact paragraphs.
- Prefer small code blocks and tables only when they clarify exact mappings.
- Use GitHub-flavored Markdown and admonitions only for material warnings.
- Actively inspect CI configuration, manifests, runtime or toolchain
  declarations, package metadata, executable names, and supported-platform
  configuration for stable badge candidates.
- Add a compact badge row immediately below the title when at least one stable,
  verifiable, user-useful fact is suitable for a badge. The absence of badges in
  the existing README is never a reason to omit them.
- Prefer badges for facts such as build status, primary runtime or toolchain,
  package or executable identity, released package version, or intentionally
  bounded platform support.
- Preserve useful existing badges only when they remain verified and relevant.
- Keep badges few, visually consistent, and maintainable. Omit decorative,
  redundant, stale, unverifiable, or high-maintenance badges.
- Link each badge to the most relevant authoritative website, project
  documentation, CI page, package page, or README section instead of leaving it
  as an image only.
- Avoid marketing copy, generic claims, excessive headings, and emoji.
- Use a logo or screenshot only when it already exists, is meant for public
  use, and materially improves identification or understanding.
- Do not add `License`, `Contributing`, or `Changelog` sections when dedicated
  files own that content.
- Avoid bare URLs when a descriptive Markdown link is clearer.
- Keep examples reproducible and free of secrets, credentials, and
  machine-specific private data.

## Validate without causing side effects

1. Verify documented commands and values against source.
2. Run only safe, relevant checks allowed by the applicable `AGENTS.md`.
3. Do not run deployment, bootstrap, package installation, setup, cleanup,
   sync, or other live mutations merely to validate prose.
4. Run the repository's Markdown lint command when available.
5. Check relative links, fenced blocks, tables, and placeholders.
6. Run `git diff --check`.
7. Re-read the finished README for duplicated companion content, stale
   inventory, invented behavior, and unnecessary sections.
8. Re-check the finished README against every applicable rule in this skill.
9. In **Rewrite** mode, confirm that the final structure was re-derived from
   repository evidence instead of mechanically inherited from the previous
   README, and that the result is a coherent replacement rather than a patched
   version of the old document.
10. If stable badge-worthy facts exist, confirm that an appropriate badge row is
    present. If badges are omitted, the repository must lack a reliable,
    user-useful badge candidate under the rules above.

Finish with a concise summary of what changed, what was validated, and any
claim that could not be verified.
