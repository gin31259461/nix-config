# Commit messages and history finalization

Read during planning to choose the final history, and again before committing or
rewriting task commits. Local task-history cleanup belongs to the approved plan.
Publishing, merging and rewriting shared history have their own authorization.

## Resolve the repository's convention

Read applicable instructions, CONTRIBUTING, commit-message tooling and recent
accepted commits affecting the relevant area. Determine allowed types, scope
rules, length limits, breaking-change syntax, trailers, signing and merge policy.
Documented rules and executable checks outweigh inconsistent historical examples.

If no repository policy exists, use this skill's default:

```text
type(scope): imperative summary

Explain the concrete problem and why this change solves it.
Add compatibility or migration details when they matter.

Applicable trailers
```

Use a meaningful scope naming the owning subsystem. The default requires it;
Conventional Commits itself makes scope optional. If the repository requires a
different format, surface the difference in the plan and use the agreed
repository-compatible convention. Do not change commitlint or contribution policy
merely to accommodate this skill.

For the default format:

- Use `feat` for new behavior, `fix` for a defect, `perf` for a performance change,
  `refactor` for behavior-preserving restructuring, `docs` for documentation,
  `test` for tests, and `build`, `ci` or `chore` for their respective maintenance.
- Keep the header within 72 characters unless the repository sets another limit.
  Use an imperative verb, normal identifier capitalization and no terminal period.
  Prefer English unless the repository or developer specifies another language.
- Describe the final effect. Avoid `update stuff`, `fix review`, `WIP`, milestone
  numbers, agent names and transcripts of the development process.
- Add a body when rationale, tradeoffs or compatibility would otherwise be lost.
  Do not pad a trivial change with boilerplate or require a large template.
- Mark genuine breaking changes with the repository's required syntax and explain
  the migration. Preserve applicable issue references and attribution; do not
  invent issue numbers, coauthors, sign-offs or statements of legal certification.

Examples of the default style:

```text
fix(parser): reject unterminated quoted values
feat(cache): expire entries after the configured lifetime
refactor(storage): isolate retry policy from the transport
docs(cli): explain offline initialization
```

A feature's tests and docs normally belong with that feature. Do not classify a
functional change as `chore` to avoid thinking about its public effect. Honor
existing hooks and signing requirements; never disable them to make a commit pass.

## Define the history boundary before development

Record the starting branch and exact HEAD, pre-existing staged/unstaged changes,
known publication state and authorized final commit structure. Track the hashes
and paths of commits created for this task. A range such as "last five commits"
or all commits since a guessed merge-base does not establish task ownership.

Stage only task-owned paths or reviewed hunks. Review the staged diff before
every commit. Do not use blanket staging to absorb pre-existing work. Missing Git
identity is a concrete configuration issue; do not invent an author or change
global Git settings to bypass it.

Development commits may be useful checkpoints. Prefer a coherent change paired
with tests, and use targeted fixup commits when the repository supports that
workflow. Record that temporary fixups will be folded during finalization.

If several commits were planned, finalization must proactively inspect and
organize them after all implementation, documentation and required verification
are complete. Default to one final commit for the accepted task. Keep a short
logical series only when the approved plan calls for independently reviewable
changes. Already-correct final commits need no pointless rewrite; explain that
the history was reviewed and already matched the plan.

## Establish that rewriting is eligible

Before changing history, verify all of the following:

1. Implementation writers have finished. No concurrent Git writer or merge,
   rebase, cherry-pick or revert operation is in progress.
2. The exact base is an ancestor of the task tip. Every commit to rewrite is
   attributable to this task and belongs to the approved rewrite range.
3. The selected range has no unrelated or unexplained commits and no merge
   topology that the chosen method would flatten accidentally.
4. The working tree and index in the rewrite checkout are clean. Unrelated
   staged, unstaged and untracked work remains preserved; do not auto-stash,
   delete or commit it to satisfy this precondition.
5. The commits are local and unpublished, or this exact shared-history rewrite
   is already authorized. Check known refs and publication evidence. A missing
   upstream or stale remote-tracking refs do not prove a commit was never shared.

Inspect targeted Git state and refs; do not dump configuration or remotes that
may contain credentials. Use existing remote access only when appropriate, and
do not infer permission to force-push from permission to edit local history.

When a condition is not met, first look for an in-scope way to finish safely,
such as an allowed isolated checkout of a proven task-only range. Do not rewrite
unrelated commits even if their final files would be unchanged. If history
cleanup needs a material scope decision, prepare the exact proposed range,
messages and alternative, then ask. Finish other approved work in the meantime.
Report unfinished cleanup as unfinished, not as completed squashing.

## Rewrite with recovery and content checks

Record the pre-rewrite tip and tree ID, then create a unique local recovery ref
at that exact tip. Check that the ref does not already exist; do not overwrite an
existing recovery point. A recovery ref protects committed history, not dirty
files. Preserve it until the result is accepted and report its name in the handoff.

Choose the method based on the approved shape:

- For a logical series with fixups, use an explicit, inspected interactive-rebase
  todo or autosquash over the exact task range. Fixup messages must resolve to the
  intended commits; duplicated subjects make blind autosquash unreliable.
- For one final commit, an inspected rebase can fold the task range, or a soft
  reset to the verified task base can stage its aggregate diff for recommitting.
  A soft reset changes HEAD and is a history rewrite; it is not harmless merely
  because it preserves file content. Apply the same eligibility checks.

Do not use a hard reset, clean, blanket checkout, `rebase --root`, or automatic
stashing as a shortcut. Control rebase options that could update other refs or
pick a different base. Prefer explicit `--no-autostash`, `--no-update-refs` and
an exact approved base where supported. Review the intended todo before running
it; never inject untrusted commit subjects into shell commands.

Construct the final message from the complete accepted change rather than
concatenating checkpoint messages. Preserve meaningful authorship and existing
trailers when combining work. A squash changes commit IDs and cannot preserve
the old signatures; honor the repository's signing requirements for new commits.
If authorship or required certification is unclear, resolve that specific issue
before creating a misleading commit.

If a rewrite fails or conflicts, stop mutation, inspect the state and preserve
diagnostics. Use the in-progress operation's normal recovery path within the
approved scope. Never skip a commit or discard a hunk merely to finish squashing.
Use the available merge-conflict skill when applicable. Recheck the result after
any resolution; do not assume an intended history-only edit stayed content-only.

## Verify and hand off

Compare the final tree ID with the pre-rewrite tree ID for a history-only cleanup.
Also inspect the aggregate diff from the recorded task base and the final commit
list. Verify the intended parent/base, message format, preserved attribution,
absence of leftover fixup/WIP commits and preservation of unrelated work.

Run the repository's commit-message checks on the final messages. If content is
identical, earlier content-test results remain applicable unless repository policy
or commit-derived behavior requires rerunning them. Rerun affected checks if
hooks, conflict resolution or other work changed the content. A final tree match
does not prove intermediate commits build; validate retained commit boundaries
when that is part of the agreed series contract.

Report the final hashes and subjects, checks, any remaining limitation, and the
recovery ref. If rewriting fails after a soft reset, remember that task changes
may be staged while HEAD points to the base; report and recover that actual state.
Do not claim a clean working tree when preserved unrelated changes remain.

Do not automatically push, force-push, open or merge a PR, remove branches or
delete recovery refs. If publication is already in the user's scope, follow that
authorization and the repository's policy. A hosted squash merge creates a
different commit on the target branch; a tidy local history is not evidence that
the PR was merged or deployed.
