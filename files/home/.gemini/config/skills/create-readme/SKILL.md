---
name: create-readme
description: Create, rewrite, refresh, or audit repository READMEs with verified quick starts, project-appropriate structure, and relevant badges and visuals. Use for project documentation, not profile READMEs or unrelated docs.
---

# Create a repository README

Make the README a reliable front door: readers should understand the project,
decide whether it fits, reach a first useful result, and find their next step.
Optimize for those outcomes and maintainability, not section count or decoration.

## Match the requested scope

Create from evidence when absent; rewrite the whole document when requested;
refresh only the requested material for a focused update. Audit produces findings
without edits unless authorized. A rewrite reassesses substance and organization
but may preserve an already effective outline.

Respect the user's audience, language, tone and visual preferences. Otherwise,
follow the repository's established language and presentation. For restoration,
use history to recover style while retaining current facts and commands; never
restore an old file wholesale. Preserve useful branding, previews and badges
unless they are obsolete, misleading or the user requests a change.

For a new document or substantial rewrite, read
[structure and examples](references/structure-and-examples.md). When adding,
changing or auditing badges or visuals, also read
[badges and visuals](references/badges-and-visuals.md). These are decision aids,
not mandatory templates. Browse the linked examples only when current external
facts or a requested comparison require it.

## Establish what the repository actually offers

Read applicable instructions, Git status, the existing README and relevant
companion documents. Find the owning source if the README is generated or managed
elsewhere. Identify which README is surfaced on the hosting platform and whether
package publication or translations introduce another audience or path context.
Do not overwrite unrelated changes or silently broaden the documentation task.

Build a small working evidence map; it need not become a repository artifact:

| Question | Inspect |
| --- | --- |
| Who is this for, and what problem does it solve? | Public interfaces, examples, existing docs and explicit project policy |
| How does a reader obtain and use it? | Package/release metadata, CLI source, entry points and example fixtures |
| Which prerequisites and environments are supported? | Consumed manifests, toolchain configuration, CI and support policy |
| What configuration changes behavior? | Typed schemas, defaults, validation and actual callers |
| How are changes validated? | Task definitions, tests, CI jobs and contribution guidance |
| Which claims and visuals are trustworthy? | License files, actual workflows, releases, assets and their destinations |

Read task bodies and called scripts, not only task names. A lockfile is evidence
of resolved dependencies, not a promise of supported runtime versions. A CI
matrix shows tested environments, not necessarily the complete support policy.
Distinguish source-checkout instructions from released-package instructions.

Resolve conflicting documentation against implementation and explicit policy.
When policy describes a requirement the code violates, report that discrepancy;
do not silently redefine the policy. Qualify or omit unsupported claims. Never
invent installation routes, flags, support guarantees, licenses or benchmarks.

## Design the reader's path

Before drafting, identify the primary reader, their first useful outcome, the
main prerequisite, and the next destination after success. Prefer this sequence
when creating an outline:

1. Identity and purpose, with the decisive compatibility or maturity caveat.
2. A compact proof of usefulness: example, screenshot or concrete capabilities.
3. One recommended quick start with a visible success condition.
4. Common workflows and essential configuration.
5. Links to deeper docs, development, help and verified license information.

Combine, omit or reorder sections to fit the project. A small library may need
only a description, complete example and links. A workstation configuration may
need host assumptions and a preview before its first activation instructions.
Put adoption blockers before the steps they invalidate. Do not bury first use
beneath an exhaustive feature list, architecture essay or contributor setup.

Keep tutorial steps, operational procedures, API reference and architectural
explanation distinguishable. Link to their existing homes instead of copying
them all into the README. README introduces public workflows; AGENTS governs
agent changes; architecture documents explain composition; runbooks own detailed
operations and recovery. Create companions only when authorized and useful.

## Write a complete first-use workflow

Give the reader a continuous path from the stated starting conditions to success:

- State required tools, supported environment, working directory and necessary
  configuration before use. Derive version requirements from owning evidence.
- Choose one supported default installation route. Put alternatives nearby or
  link to them; clearly label platform-specific commands and shell syntax.
- Include required file contents, imports, flags and minimal synthetic input.
  Keep essential steps visible. Avoid unexplained placeholders or ellipses in
  a block presented as runnable; identify values the reader must supply.
- Show how to verify success: an expected response, generated artifact, visible
  UI result or relevant status. Keep sample output separate from copyable commands.
- Explain relevant writes, privileges, network use or live changes immediately
  before the responsible step. A development server is not a production recipe.

Prefer checked-in examples or supported public APIs. Keep commands usable as
written: quote shell-sensitive values, name files, and avoid requiring readers
to infer hidden setup. Do not replace a real application screenshot with a
fabricated UI. Keep secrets and private machine information out of all examples.

Explain capabilities in terms of reader outcomes. Describe limitations honestly;
mark planned work as planned. Separate declared configuration, built artifacts
and observed runtime state. Passing tests does not establish that a planned
feature exists or that a deployed system is healthy.

## Make the presentation earn its space

Use descriptive headings, concise paragraphs and fenced examples with language
labels. Use tables for comparisons and mappings, lists for parallel choices, and
diagrams only when they clarify a relationship. Add a short contents section when
it aids navigation; a small README does not need a second outline.

Include badges only for useful, verified information, each with meaningful alt
text and a relevant destination. Keep the opening readable with images disabled.
Preserve valid existing assets and recognizable style; do not add a wall of
technology logos, unmeasured quality claims or empty template sections.

Keep volatile inventories in their owning source. Summarize the capabilities a
reader needs and link to the authoritative list. Avoid reproducing entire command
help, dependency lists or directory trees unless they solve a navigation problem.
Preserve attribution and verified legal information when reorganizing content.

## Validate the reader experience

Review as a reader with only the declared prerequisites. Trace every quick-start
step to its definition and confirm that it leads to the stated result. Execute
safe examples in isolation when appropriate; inspect first for side effects.
Do not deploy, activate, register, install system packages or clean application
data merely to validate documentation. Report examples checked against source
separately from examples actually executed.

Check relative links, case-sensitive paths, heading anchors, image targets,
reference definitions, code fences and tables. Use the repository's Markdown
checks and `git diff --check`. Where tooling permits, preview rendered Markdown
for heading hierarchy, narrow layouts, image sizing and light/dark readability.
Check external links and badge meaning when accessible; report unavailable
verification rather than treating an authentication or network failure as proof
that a resource does not exist.

Before finishing, confirm:

- The opening answers what it does, who it serves and why to use it.
- First use has no hidden setup and includes an observable success condition.
- Commands, support claims, badges and examples match their evidence.
- Essential warnings precede the affected action; detailed docs remain findable.
- The rewrite retains valid facts, attribution and useful presentation assets.
- No placeholders, invented claims, broken local links or duplicated inventories
  were introduced.

Summarize the substantive changes and validation, including meaningful removals
and unresolved facts. Do not imply runtime verification or deployment occurred
when only documentation was checked. Commit or push only within authorized scope.
