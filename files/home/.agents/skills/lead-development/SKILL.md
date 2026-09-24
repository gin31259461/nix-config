---
name: lead-development
description: Lead substantial development through a complete plan, developer discussion, explicit execution approval, implementation, verification and clean commits. Use for end-to-end feature, fix or refactor work that needs this lifecycle, not isolated reviews, diagnosis-only requests or quick edits.
---

# Lead development

Act as the primary development coordinator. First establish a complete,
repository-grounded plan, discuss implementation choices with the developer, and
wait for their explicit instruction to execute that plan. Then carry the approved
work through implementation, verification, documentation and history cleanup.

This skill defines a workflow for a development task. Creating, editing or
reviewing the skill itself does not start an implementation task or authorize
committing unrelated work in the current checkout.

## Phase agents and coordination

Use these subagents with explicit model and reasoning-effort settings:

| Phase | Model | Effort | Deliverable |
| --- | --- | --- | --- |
| Plan | `gpt-6-astra` | `xhigh` | Evidence, complete proposed plan, dependencies and acceptance criteria |
| Discuss | `gpt-6-sol` | `medium` | Implementation tradeoffs, focused questions and revised decisions |
| Develop | `gpt-6-luna` | `medium` | Implemented slices, relevant tests, docs and verification results |
| Finalize | `gpt-6-sol` | `medium` | Independent completion review, final commit organization and handoff |

The primary agent keeps the user conversation, approval state, integration and
overall completion responsibility. These settings select phase subagents; they
do not switch the primary agent's model. Pass both model and effort when the
tool allows it. If a required combination or delegation is unavailable, explain
the precise limitation and ask for a supported alternative. Do not silently
replace a model, inherit an unintended default or claim an agent ran when it did
not. Continue independent evidence gathering while that choice is pending.

Read [planning and handoffs](references/planning-and-handoffs.md) before planning
or resuming a substantial task. Read [commit history](references/commit-history.md)
when designing the commit plan and before any commit or rewrite. Consult
[sources and evaluation](references/sources-and-evaluation.md) when auditing this
workflow or validating its behavior.

Give each child a bounded task, relevant evidence, applicable instructions, owned
paths, allowed mutations and an expected result. Do not recursively invoke the
whole workflow inside a child. Coordinate shared files and use a single Git
writer. Phase delegation should run alongside useful primary-agent inspection,
discussion preparation, integration or verification.

## 1. Investigate and plan

Read repository instructions, the relevant architecture and public docs, Git
status, implementation, tests and task definitions. Preserve existing staged,
unstaged and untracked work. Record the starting branch and HEAD and establish
which changes belong to this task before any implementation.

Have the planning agent produce a concrete proposal covering:

- Intended outcome, observable acceptance criteria, scope and exclusions.
- Current behavior with source evidence; assumptions and unanswered questions.
- Recommended design, ownership, interfaces, error handling and compatibility.
- Material alternatives and the tradeoffs the developer needs to decide.
- Ordered implementation milestones, dependencies and integration points.
- Exact validation appropriate to the risk, including setup and side effects.
- Necessary README, docs or AGENTS updates.
- Development checkpoints and the final commit or logical series to retain.

Scale the plan to the work. Avoid speculative abstraction or a task list that
only says “implement, test, document”. Do not invent contracts or commands. Keep
the initial phase read-only except for a planning artifact the user requested.
Use the conversation or the project's existing planning location; do not create
issues, publish plans or add new planning directories without task authority.

## 2. Discuss and obtain execution approval

Have the discussion agent assess the proposal and identify unresolved design
choices. Present the complete plan and its recommendations to the developer,
explain relevant tradeoffs, and incorporate their answers into a clear revised
version. Do not ask questions the repository already answers.

Wait for explicit developer approval of the concrete plan before implementation.
An answer to a design question, an earlier broad feature request, silence or a
subagent's approval is insufficient. If approval is pending, finish useful
read-only planning and end with the specific execution question. Explain that
this planning gate is part of this workflow; do not claim a tool blocked you.

Approval includes the local commit/finalization scope described in the plan.
Preserve approval across subagent handoffs, compaction, retries and routine
implementation adjustments. Do not ask again when it is already established.
An explicit user change to this workflow takes precedence over its default gate.

If new evidence requires a material change in scope, public behavior, architecture
or external effects, discuss that change and obtain the needed decision before
dependent work proceeds. Continue independent work covered by the existing plan.
Implementation approval does not silently authorize publishing, deployment,
messaging or rewriting shared history; honor any authority already given.

## 3. Implement until the accepted task is complete

After approval, give the development agent the approved plan and exact ownership
boundaries. Work through the milestones, integrate results and resolve failures.
Use multiple development agents only for independent slices with disjoint edits
or explicit integration ownership. Respect actual concurrency limits.

Prefer the repository's existing abstractions and commands. Add meaningful tests
for changed behavior where appropriate; avoid tests that merely repeat production
inventories or freeze private implementation. Run focused checks during work and
the required integrated checks when the result is ready. Track what actually ran
and which tree or commit it verified.

Handle relevant documentation as part of the accepted work:

- Use `create-readme` for README creation, substantial rewrites or audits needed
  by the change. Load the available skill before editing under its guidance.
- Use `create-agentsmd` when ownership, editing contracts or validation rules
  require instruction updates. Preserve valid constraints and scope.
- Update `docs/` at its owning procedures or architecture documents. Use another
  available documentation skill only when it fits; do not treat AGENTS as a
  runbook or use a README template for every documentation file.

If a companion skill is unavailable, disclose that and apply its relevant
document responsibilities directly; do not install it or abandon otherwise
authorized work automatically. Companion workflows must preserve this task's
existing approval and do not create authority for unrelated external actions.

Continue through fixes, tests and necessary docs without routine milestone
confirmation. A status question is a request for an update, not cancellation.
Pause only for a concrete decision, missing authority or external dependency
that prevents further in-scope progress. Report that blocker and the completed
portion accurately; do not relabel remaining requirements as optional.

## 4. Verify, finalize and organize commits

Have the finalization agent review the integrated result against the approved
plan, repository constraints and actual validation evidence. Check for missing
behavior, regressions, stale docs, lost constraints and unintended changes. Fix
actionable findings through the development phase before history cleanup.

When multiple development commits were planned or created, proactively finalize
them after implementation, documentation and required checks are complete. Use
the approved structure: normally one coherent task commit, or the explicitly
agreed logical series with fixups folded into their owning changes. Do not leave
WIP or review-fix chatter in the final history and merely offer to squash later.

Follow the repository's commit convention strictly. When none exists, use
`type(scope): imperative summary` with a meaningful subsystem scope, accurate
change type and a concise description of the resulting behavior. Explain
non-obvious motivation or compatibility in the body. Do not invent attribution,
sign-offs or issue references.

Before rewriting, use the eligibility and recovery procedure in
[commit history](references/commit-history.md). Rewrite only the proven,
authorized task range; preserve unrelated changes, commits and other refs.
Record a recovery ref and verify that history-only cleanup preserves the tested
tree. Published or ambiguously owned history needs the specific authority already
given or a concrete decision; never infer it from “keep history clean”.

Keep one Git writer while the finalization agent reviews and prepares messages.
Do not bypass commit hooks or signing requirements. Do not push, merge, deploy
or remove recovery refs unless that action is already within the user's scope.

## Completion and handoff

Finish only when the accepted behavior is implemented, required checks are
satisfied, relevant documentation is current, the integrated diff has been
reviewed, and eligible planned history cleanup is complete. Preserve unrelated
work. If a required item is blocked or unverified, say exactly what remains
instead of claiming the whole task is done.

Give the developer a concise handoff: what changed, verification and limitations,
final commit hashes/subjects, relevant recovery reference and any concrete
remaining decision. Distinguish source validation from live activation and local
commits from publication. Do not end with an offer to perform a normal remaining
step that is already approved and still possible.
