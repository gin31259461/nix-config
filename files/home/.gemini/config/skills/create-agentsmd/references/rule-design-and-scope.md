# Rule design and scope

Use for substantial instruction work, scoped exceptions or ambiguous policy.
The examples below are illustrative; their paths and commands are not defaults
to insert into another repository.

## Shape a useful rule

A rule is valuable when it links a likely decision to a project-specific answer.
Use as much of this pattern as needed: condition, action, owner, reason and
verification. Not every sentence needs all five.

| Weak instruction | More useful, if supported by the project |
| --- | --- |
| Keep generated code consistent. | Edit `schema/api.yaml`, then run the repository's generator; `src/generated/` is output. |
| Test your changes. | For parser behavior changes, run the parser fixtures through `just test-parser`; documentation-only edits use `just docs-check`. |
| Follow the architecture. | Keep transport validation in `api/`; domain functions receive validated values and must not import HTTP types. |
| Be careful with customer data. | Use synthetic records in integration fixtures; never read or print the runtime database to construct tests. |
| Do not edit vendored code. | Change the upstream source and update its pinned revision; `vendor/` is generated from that revision. |
| Avoid breaking users. | Preserve accepted configuration keys or provide the versioned migration described in the compatibility policy. |

Do not insert these rules unless their ownership, commands and policy actually
exist. A general preference for a pattern is not evidence that a repository
requires it. A prohibited action often needs an alternative so an agent can
continue productively.

## Distinguish policy, facts and advice

An explicit "retries must retain the recovery marker until success" is a policy
even if a buggy implementation deletes the marker early. Preserve the contract
and report the mismatch. Do not rewrite it as "markers are deleted on failure"
just because that describes current code.

A task runner calling a formatter is an implementation fact. Inspect whether the
task checks or rewrites files before labeling it safe validation. A single test's
use of a mocking library is a local example, not automatically a ban on other
test methods. A roadmap does not establish an implemented architecture.

When evidence conflicts, investigate the owner and current policy. If a remaining
choice would change a material requirement, surface that choice while completing
independent, supported improvements. Do not use uncertainty about one sentence
as a reason to abandon the entire task or silently invent policy.

## Design the instruction scopes

| Scope | Appropriate content | Common mistake |
| --- | --- | --- |
| Repository root | Shared ownership boundaries, common checks and critical constraints | A catalog of every file and every package command |
| Package or subtree | Different test runner, generated-source rules or a local exception | Copying all root guidance or silently contradicting it |
| Global user guidance | Cross-project preferences explicitly requested by the user | Promoting one project's choices into unrelated repositories |
| Linked reference | Background, long procedures and detailed explanation | Hiding a critical constraint behind an unlabeled link |

Create a child file when the difference changes how work should be done there.
For example, frontend snapshot updates and database migration checks may need
different commands. Shared secret-handling rules usually belong in their common
parent. Avoid a child file containing only "follow the root instructions".

For several scopes, a short route table can name the subtree, instruction path
and trigger. Resolve relative links from the file that contains them. Check that
managed files are edited at their source and that a new child file is actually
discoverable in the intended workflow.

## Treat loader behavior as tool-specific

[AGENTS.md](https://agents.md/) defines a Markdown convention with flexible
headings and scoped project guidance. The consuming tool determines exactly how
it discovers and incorporates files. Do not imply this document can supersede
system instructions, permissions or the user's authorized scope.

In Antigravity / AGY, directory and project rules follow hierarchical discovery.
As files are opened or edited, the loader walks up from the active file's
directory to the repository root, loading matching instruction files:
`AGENTS.md`, `GEMINI.md`, and `.agents/rules/*.md`. Discovered rules are
automatically deduplicated by their resolved canonical path, preventing
redundant application when rules are inherited across parent directories.

For Codex, the [official instruction-discovery guide](https://developers.openai.com/codex/guides/agents-md/)
describes a chain assembled at run start: global guidance, then the project path
from root to the current directory. Per directory, an override file can shadow
the normal AGENTS.md; only one candidate is included. Fallback names and the
combined size limit are configurable. Verify current behavior when troubleshooting
loading; do not assume changing files reloads an existing session or that all
descendant instructions were already loaded.

This is why creating many nested files alone does not establish correct routing.
Keep important shared constraints in the common scope and provide explicit
read-before-edit routes where needed. Do not change global configuration,
increase instruction limits or create override files as a side effect of writing
repository guidance.

## Preserve meaning while reducing length

Use deletion and deduplication before compression. Keep the distinctions that
change execution:

- Check-only validation versus commands that rewrite, publish or activate.
- An optional prerequisite that has never been prepared versus corrupt or
  drifting state that must be reported as a failure.
- Disabling management versus permission to delete accounts, packages or data.
- Diagnostic completeness versus disclosure of secrets in those diagnostics.
- A fast local check versus a required full gate before delivery.

These are examples of semantic distinctions, not required policies for every
project. Retain them when the repository owns such contracts. Remove stale
workarounds only with evidence that their underlying problem or policy no longer
applies. Preserve existing exceptions and their scope.

Do not duplicate generic agent behavior such as reading code carefully or writing
clean code. Avoid arbitrary minimum tests, compulsory diagrams, fixed response
formats and universal "ask first" rules unless the user or repository requires
them. Tooling should own mechanically enforced formatting; instructions should
explain decisions that tooling cannot express well.

## Behavioral acceptance scenarios

Review outcomes, not whether the file contains particular headings or phrases.

| Scenario | Desired decision |
| --- | --- |
| README typo with no behavior change | Run the applicable documentation checks, without starting services or inventing a full-suite obligation |
| Editing a generated client | Locate and edit the source/generator, then use the documented regeneration/check workflow |
| Change spans two packages | Read both scoped rules and run the relevant checks without applying one package's exception globally |
| Existing code violates an explicit retention policy | Preserve the policy and report the discrepancy; do not quietly authorize deletion |
| A test script updates snapshots | Classify it as a writing operation, not a read-only check |
| Live operation is already authorized | Continue within that scope without adding a new blanket approval gate |
| "Rewrite" request with valuable constraints | Preserve their meaning even if wording and organization change |
| An instruction file is shadowed by an override | Report the discovery issue and edit the correct authorized source |

For a complex revision, an isolated forward test may use a small synthetic
repository and a realistic task. Keep live systems and user data out of fixtures.
If independent evaluation is available and authorized, provide the task and raw
evidence without feeding the evaluator the expected answer.

## Reference and rationale

Reviewed on 2026-09-16. The guidance here is a synthesis, not a requirement imposed
by the example projects. Recheck moving source URLs when a technical detail
matters to the target task.

- [AGENTS.md format](https://agents.md/): flexible Markdown and project-scoped
  instructions. Use it for the convention, then check the target tool's loader.
- [Codex instruction discovery](https://developers.openai.com/codex/guides/agents-md/):
  concrete discovery, precedence and size behavior for that tool.
- [Next.js AGENTS.md](https://github.com/vercel/next.js/blob/canary/AGENTS.md):
  distinguishes source from compiled output and chooses test commands by runtime
  mode and bundler. Borrow the specificity and conditional validation, not its
  full inventory, commands or repository-specific mandates.

A well-known repository is evidence of one team's needs. Its length, worktree
policy or mandatory tooling is not proof that the same choice fits another team.
