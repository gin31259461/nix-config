# Planning and phase handoffs

Read before producing the implementation plan or resuming a substantial task.
Scale the detail to the task; completeness means the material decisions are
visible, not that every function or future line of code is predicted.

## A plan the developer can approve

Ground the plan in repository evidence. Inspect relevant instructions, entry
points, interfaces, tests, build tasks and existing changes before recommending
an approach. Distinguish requirements, observations, assumptions and open choices.
Do not present intended design as current implementation.

Cover the following in a concise proposal:

| Part | Required answer |
| --- | --- |
| Outcome | What observable behavior will exist when this task is complete? |
| Scope | Which workflows and components change, and what is intentionally outside the task? |
| Current behavior | What source evidence explains the starting point and the problem? |
| Design | Who owns the change, what interfaces change, and why is this approach appropriate? |
| Tradeoffs | Which credible alternatives matter, and which choice needs the developer's judgment? |
| Delivery | What are the ordered milestones, dependencies and acceptance checks? |
| Compatibility | What happens to existing callers, configuration, persisted data and error behavior? |
| Validation | Which exact checks verify the contract, in what environment, with what side effects? |
| Documentation | Which README, docs or agent rules must reflect the resulting behavior? |
| Commits | Which development checkpoints are useful, and what final commit or series should remain? |

For higher-risk work, include migration, recovery, rollout and observability when
they affect the actual task. Avoid irrelevant security or operations checklists.
For a small change, a few paragraphs can cover the same decisions.

Make milestones coherent slices of behavior with explicit dependencies. Pair
implementation with its relevant tests and documentation rather than deferring
all verification to a final cleanup milestone. Record whether work can be split
across non-overlapping files and where one agent must integrate shared changes.

## Discuss and approve a concrete version

Present the complete proposed direction before asking the developer to authorize
implementation. Ask focused questions about meaningful tradeoffs and unresolved
constraints; do not ask the developer to rediscover facts available in source.
Offer a recommendation with reasons and summarize how each answer changes the
plan. If the requirements already settle a choice, state it without a questionnaire.

Revise the proposal into an identifiable version, such as “plan v2”. Include the
final commit policy: normally squash the task's local development commits into
one coherent commit, or retain the explicitly proposed logical series. Explain
any repository convention that conflicts with the requested commit format.

Ask whether to execute that version, including its local commit/finalization
scope. Use the available user-conversation mechanism; do not misuse a tool that
is limited to optional preference questions to request execution authorization.

Approval is an affirmative instruction to execute the presented plan. A technical
answer, a choice between alternatives, silence or a subagent's recommendation is
not execution approval. A prior request to investigate or draft a plan does not
authorize implementation. If the developer already approved this concrete plan
in the session, retain that approval and continue without asking again.

Before approval, continue read-only investigation and plan refinement. Do not
edit product source, create implementation commits, change dependencies or run
live operations. An explicitly requested planning artifact may be written in the
repository's permitted location; otherwise keep the plan in the conversation or
existing task tracking. Do not invent a new permanent planning-document tree.

If the developer explicitly changes or waives the approval workflow, honor that
instruction within higher-priority constraints and record the resulting scope.

## Preserve the task across phases and sessions

Keep a compact handoff record in the conversation or existing task facility:

```text
Objective and acceptance criteria:
Current phase and plan version:
Developer decisions and evidence of execution approval:
Authorized mutations and external effects:
Repository path, branch and starting HEAD:
Pre-existing changes and protected paths:
Task-owned paths, commits and final history policy:
Completed milestones and integrated results:
Checks, outcomes and tree/commit tested:
Remaining work, blockers and material scope changes:
```

Fill only relevant fields. Do not store secrets or copy complete logs into this
record. Preserve useful command diagnostics in appropriate task output, redacting
secrets. Do not encode task-local progress into permanent AGENTS instructions.

After compaction or resumption, recover this record and compare it with current
Git state. Do not reinterpret unrelated changes as this task's work or discard
prior approval. If the code has materially diverged, investigate and revise only
the affected decisions.

## Delegate bounded work

The primary agent owns the developer conversation, approval, integration and Git
state. Every phase agent receives a compact brief:

```text
Role and phase:
Objective and expected deliverable:
Relevant plan version, decisions and approval state:
Repository evidence and applicable instruction paths:
Owned paths and interfaces; dependencies on other work:
Permitted edits and explicitly excluded effects:
Required checks and acceptance criteria:
Return changed paths, results, unresolved choices and exact blockers.
Do not commit, switch branches or rewrite history unless designated Git owner.
Do not approve the plan on behalf of the developer or recursively orchestrate it.
```

Use the phase model and effort from SKILL.md. Create explicit bounded-context
agents when the tool requires that for model overrides; provide the necessary
facts instead of relying on unavailable conversation inheritance. Do not invent
spawn fields. Check the tool schema and actual allowed model identifiers.

Parallelize independent development slices only when their ownership is clear
and the main agent has useful coordination or integration work. Serialize shared
files, migrations, generated outputs, dependency manifests and lockfiles when
they cannot be changed safely in parallel. A shared checkout has one index and
branch: designate one Git writer and freeze writers during history changes.

Use isolated worktrees only when repository instructions allow them and the plan
accounts for their baseline and integration. A worktree does not automatically
include relevant uncommitted work. Do not switch the developer's branch, stash
their changes or copy their state to simplify delegation.

Have the discussion agent return recommendations and developer-facing questions;
the primary agent relays them and records actual answers. Have the finalization
agent review the integrated diff and acceptance evidence independently of the
implementation narrative. Route any discovered code defects back to development.

## Change direction without restarting the task

Routine implementation adjustments that preserve the approved contracts remain
authorized. Explain consequential choices briefly and continue. Reopen discussion
for material changes to the outcome, public interface, data handling, architectural
direction, cost or external effects. Pause only the dependent work while other
approved work can proceed.

If progress requires missing authority, unavailable credentials, a developer
decision or an external-state change, complete the independent in-scope work and
report the concrete blocker. Persistent execution means resolving work until the
accepted outcome is reached; it does not mean retrying an unchanged failure
forever or claiming a blocked task is done.
