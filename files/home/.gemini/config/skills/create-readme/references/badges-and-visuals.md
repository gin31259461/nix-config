# Badges and visuals

Use when adding, revising or auditing presentation assets. Keep existing useful
design unless the task calls for a change. A badge or visual should help the
reader assess compatibility, trust a specific claim or understand the product.

## Select badges by the question they answer

| Badge | Evidence required | Useful destination |
| --- | --- | --- |
| CI status | An actual relevant workflow, appropriate branch and meaningful runs | That workflow's run history |
| Published version | The correct published package or release channel | Package registry or releases page |
| License | License files and any multiple-license conditions | The actual license file or licensing explanation |
| Runtime/platform support | Declared support policy and relevant build/test evidence | Compatibility section or supported-platform docs |
| Documentation status | An actual docs build service | The documentation version represented |
| Coverage | A maintained report with a clear branch and scope | The corresponding coverage report |

A few high-signal badges often suffice; zero is valid. Prefer one compact row
when it fits the established style. Stars, downloads, sponsor and community
badges are optional audience or project choices, not proof of correctness.
Avoid badges for every technology in the dependency graph or duplicated signals.

Do not add coverage infrastructure, CI workflows, service accounts or credentials
to make a proposed badge possible. Use only verified infrastructure within the
task's scope. Never infer a MIT license or a published package from convention.

## Verify meaning as well as the URL

For each retained or new badge, establish its claim, source and destination:

1. Verify owner, repository, workflow filename, package identifier and branch.
   A fork may intentionally show upstream information; label that clearly instead
   of silently presenting upstream status as the fork's status.
2. Use a live status endpoint for changing facts such as CI, versions and coverage.
   A static green passing badge cannot substantiate a successful build. Reserve
   static badges for supported descriptive facts that maintainers can keep current.
3. Confirm the image displays the intended label/value. An HTTP 200 response can
   still contain an error, unknown status or unrelated result. A failing status
   is valid information; do not hide it by changing the badge to static green.
4. Check that the click target explains the same signal. CI links to its workflow;
   license links to its terms. Include meaningful alt text, not just "badge".
5. Consider readers without the author's authentication. Do not leak tokens,
   private hosts or internal identifiers into public badge URLs or a third-party
   image service. If access or networking prevents verification, state that limit.

The [GitHub workflow badge documentation](https://docs.github.com/en/actions/how-tos/monitor-workflows/add-a-status-badge)
describes workflow-file URLs and branch/event parameters. Choose scope
intentionally: absent a branch filter, the default-branch status is used, with a
fallback to another branch if the default branch has no runs. Private-repository
workflow badges are not publicly accessible.

Illustrative syntax only; substitute values verified from the target repository
before inserting a badge. `OWNER`, `REPO` and `ci.yml` are not defaults:

```markdown
[![CI][ci-badge]][ci-runs]

[ci-badge]: https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg?branch=main
[ci-runs]: https://github.com/OWNER/REPO/actions/workflows/ci.yml?query=branch%3Amain
```

[Shields.io's static badge reference](https://shields.io/badges/static-badge)
documents label/message/color syntax and escaping. Encode values with the
service's rules; do not concatenate raw branch names or labels. Confirm supported
logo identifiers instead of guessing. Prefer a restrained, consistent style
that remains readable in light and dark themes. Color alone must not carry the
meaning.

## Choose an appropriate visual

| Reader need | Usually useful | What to verify |
| --- | --- | --- |
| Recognize the product | Existing logo or wordmark | Asset ownership, readable size and contrast |
| Understand a UI | Current screenshot or short demonstration | Actual behavior, synthetic data and a descriptive caption |
| Understand CLI output | Small input/output example, occasionally terminal recording | Copyable text alternative and matching command behavior |
| Follow architecture or lifecycle | Small diagram of verified relationships | Labels match source; renderer supports the format |
| Assess performance | Reproducible benchmark figure | Method, workload, versions and a link to the evidence |

Prefer repository-owned assets with relative links when they work in the target
renderer. Account for package-registry rendering if the same README is published
there. Use existing public external assets only when appropriate and stable;
do not reuse another project's logo or screenshots as this project's identity.

Supply useful alt text and, when needed, a caption. Keep essential instructions
as text. Check width, light/dark contrast and legibility on narrow screens. Avoid
large animated assets, unnecessary HTML and nested collapsed sections. Use
`<details>` for secondary alternatives, not prerequisites or critical warnings.

Preserve valuable preview images and their links during prose rewrites. If an
asset is obsolete, replace or remove its reference deliberately and mention the
change. Do not delete shared assets without checking their callers. Do not
generate a pretend screenshot to represent an interface that has not been built.

## Acceptance scenarios

- A repository without CI gets no invented build badge.
- A private repository gets no token-bearing badge URL or public metadata leak.
- An existing valid preview survives a text refresh unless removal is requested.
- A license badge reflects the actual terms, including multiple-license choices.
- A changed heading keeps navigation and visual links working.
- An unavailable badge endpoint is reported as unverified, not declared valid
  based solely on plausible syntax or deleted solely because the request failed.
