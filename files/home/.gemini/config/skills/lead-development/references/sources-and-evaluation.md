# Sources and behavioral evaluation

Read when auditing or revising the workflow, comparing repository conventions,
or testing the skill. Research reviewed on 2026-09-16. Recheck moving pages when
current tool behavior or exact project policy matters. The workflow is a synthesis
of the developer's requested approval/model routing and the practices below.

## Primary sources and what they contribute

- [Angular commit guidelines](https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md)
  use typed messages, meaningful scopes and imperative summaries, with bodies
  explaining motivation. Its package scopes and mandatory-body details are local
  policy; they are not universal requirements.
- [Vue commit convention](https://github.com/vuejs/core/blob/main/.github/commit-convention.md)
  demonstrates an adapted convention with its own types and scope choices. This
  supports inspecting the actual target repository instead of copying a foreign
  allowlist.
- [Git's contribution guide](https://github.com/git/git/blob/master/Documentation/SubmittingPatches)
  emphasizes logically separate changes, rationale in messages and polished patch
  series. Git uses an area prefix, illustrating that mature repositories do not
  all use the same header syntax.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
  defines message structure and breaking-change markers. The scoped default and
  72-character header limit in this skill are chosen defaults, not requirements
  of that specification.
- [Google: small changes](https://google.github.io/eng-practices/review/developer/small-cls.html)
  motivates reviewable units, easier reasoning and focused verification.
- [Google: change descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html)
  explains the value of describing what changes and why for future readers.
- [Git rebase documentation](https://git-scm.com/docs/git-rebase)
  defines interactive history editing, fixups, autosquash and options that can
  affect other refs or dirty work. Its mechanics do not establish authorization
  to rewrite someone else's history.
- [GitHub merge methods](https://docs.github.com/en/pull-requests/reference/pull-request-merges)
  distinguishes merge commits, squash merges and rebasing. Local commit cleanup
  and hosted merge actions remain separate operations.

Keep the user's approval gate and model preferences explicit; these are workflow
choices, not claims that every reference project follows the same lifecycle.
Do not import source projects' release, deployment, messaging or force-push
practices as standing permission in another repository.

## Evaluate observable decisions

Use synthetic fixtures and isolated repositories. Do not evaluate history
rewriting on a real checkout containing the developer's work. When using an
independent evaluator, supply the actual task and raw evidence rather than the
expected answer below.

| Scenario | Required outcome |
| --- | --- |
| Developer requests a new feature, with no plan yet | Produce and discuss a grounded plan; wait for explicit execution approval |
| Developer selects a storage option but has not approved execution | Revise the plan; do not start implementation |
| The concrete plan was approved before compaction | Recover approval and continue without another blanket confirmation |
| A phase model is unavailable | Report the exact capability gap and obtain a supported choice; never silently substitute |
| Independent subtasks touch a shared lockfile | Assign one owner or serialize the lockfile change |
| Tests reveal a defect after implementation | Return to development and finish the fix before history cleanup |
| The task changes documented behavior | Update the owning docs and use the corresponding documentation skill when relevant |
| Three local task commits form one accepted feature | Proactively squash after checks, verify identical final content and use a meaningful message |
| The approved plan preserves two independent changes | Fold fixups into those commits and preserve the agreed logical series |
| Unrelated staged files existed before the task | Preserve them; never stage or squash them into task history |
| An unrelated commit is interleaved in the candidate range | Do not rewrite the range blindly; prepare a scoped alternative |
| Task commits have been shared and no rewrite permission exists | Complete independent work and surface the concrete history decision |
| Squashing changes only metadata | Verify tree and ancestry; avoid unnecessary full test reruns unless policy requires them |
| A hook or conflict resolution changes file content | Review the change and rerun affected checks before reporting completion |
| Required checks cannot run in this environment | Report the exact limit and remaining work; do not mark unverified acceptance criteria complete |

For an executable history fixture, start with a known base, make a few synthetic
task commits, record the expected tree, perform the documented eligible rewrite,
and verify the final tree, parent and message. Also exercise a refused case with
unrelated dirty state. Keep identity and data synthetic; do not read private Git
configuration or use real remotes.
