# Structure and examples

Use for new READMEs, substantial rewrites and structure audits. Choose an outline
from the reader's needs; these patterns are not headings to paste indiscriminately.

## A strong default architecture

The opening should make the project legible before asking the reader to invest
in setup. A useful default is:

| Position | Reader's question | Useful content |
| --- | --- | --- |
| Opening | What is this, and is it for me? | Name, one concrete description, audience and a decisive support or maturity constraint |
| Evidence | What can I accomplish? | A small example, authentic preview or a few distinctive capabilities |
| Quick start | How do I get a first result? | Prerequisites, one supported setup path, minimal use and how to recognize success |
| Everyday use | How do I do my real task? | Common workflows, important configuration and relevant limits |
| Next steps | Where do I go deeper? | Targeted documentation, contributor entry, help and license links |

Badges and a few navigation links can sit near the identity. The first useful
example should not depend on the reader traversing every later section. Move a
limitation earlier when it changes whether or how a reader should begin.

This order is a design recommendation, not a standard. Preserve a working
existing structure when changing it would not improve the reader's path.

## Adapt to the project

| Project type | Emphasize | First useful result | Usually link out |
| --- | --- | --- | --- |
| Library or SDK | Supported runtime, package import and API shape | Complete example with output or assertion | Full API, optional integrations and advanced configuration |
| CLI | Purpose, installation, input/output and shell compatibility | A small command on synthetic input | Full flags, shell integration and advanced pipelines |
| UI or application | Authentic preview, who uses it and hosted/local choices | Open the app and complete one visible task | Deployment, architecture and contributor tooling |
| Service | Dependencies, local setup, configuration and API boundary | Start locally and verify a request | Production operations, security model and recovery |
| Dotfiles or infrastructure | Supported hosts, ownership, prerequisites and side effects | Inspect or build, then follow the supported apply procedure | Detailed operations, recovery and exact inventories |
| Monorepo | What the workspace delivers and which package to choose | Reach the relevant package's start guide | Per-package examples and implementation details |
| Template | Resulting project and what to replace | Create an instance and run it | Optional variants and upstream tooling manuals |
| Research or data project | Question, provenance, reproduction and resource needs | Reproduce one small result | Full experiments, datasets and methodology |

For a personal configuration, say so when it materially limits portability.
Avoid presenting host-specific paths or accounts as a universal installer.
For a monorepo, separate root contributor setup from consumer installation of an
individual package. For research, cite existing papers or dataset terms without
inventing a citation format or a license.

## Develop one path fully

An effective quick start establishes starting conditions, gives ordered actions,
and verifies a result. It does not need to teach every option. In a service, that
may mean installing declared dependencies, creating minimal configuration,
starting locally, and checking a documented endpoint. In a library, it may mean
one dependency declaration, a complete source file, and its output.

Use the project's actual commands. Never infer a `start`, `test`, `--dry-run` or
`--help` interface solely from ecosystem convention. A dry-run flag needs evidence
of what it guarantees. If an executable runs initialization on import or startup,
even a help command may have side effects.

If public documentation intentionally targets a released version, verify examples
against that release. Do not mix unreleased checkout behavior into the release
quick start without labeling it. Show advanced alternatives after the default
path and keep build-from-source instructions out of consumer setup unless needed.

## Choose supporting sections deliberately

- Features earn space by distinguishing useful capabilities; omit generic claims
  such as easy, powerful or production-ready without concrete support.
- Configuration should explain entry points, essential options and precedence.
  Prefer a small example over a copy of every setting. Never describe a metadata
  file as authoritative when the program does not consume it.
- Architecture belongs in the README only to the depth needed to use or navigate
  the project. A short ownership table or real dependency diagram can suffice.
- Development should point to the canonical setup and checks. Link CONTRIBUTING
  if it exists rather than creating a second contribution policy.
- Troubleshooting should cover observed, common failures with a next action.
  Avoid speculative FAQs and unsafe cleanup recipes.
- Support should route questions, bugs and private security reports through
  existing channels. Do not invent support commitments or contact details.
- License should match actual license files, including dual licenses. Public
  hosting alone does not establish a license.

Preserve a maintained changelog, roadmap, sponsor section or translations when
useful. Do not manufacture any of them to complete an outline. Preserve stable
section anchors when practical; if headings change, update known inbound links
or add a compatible anchor when the renderer supports it.

## What the reference projects teach

Reviewed on 2026-09-16. These are selected strengths, not a ranking or an
endorsement of every section. Their branch URLs change; recheck current source
before borrowing technical facts. The recommendations above are a synthesis.

| Primary source | Observed strength | Transferable choice |
| --- | --- | --- |
| [uv README](https://github.com/astral-sh/uv/blob/main/README.md) | Separates project, script, tool and interpreter workflows, with short examples and deeper links | Group examples by reader task and give each a clear next destination |
| [fzf README](https://github.com/junegunn/fzf/blob/master/README.md) | Uses a preview to explain an interactive tool, then organizes installation and integrations | Let authentic visuals explain interaction; separate platform and integration choices |
| [Serde README](https://github.com/serde-rs/serde/blob/master/README.md) | Pairs a concise library introduction with a complete serialization example and targeted documentation links | Show a real API round trip and route advanced questions to their owning docs |
| [FastAPI README](https://github.com/fastapi/fastapi/blob/master/README.md) | Connects a source file, server command and request with a visible response | Finish a quick start with a reader-verifiable result |
| [restic README](https://github.com/restic/restic/blob/master/README.md) | Demonstrates initialization and a backup, then points to restore and broader documentation | Teach the useful lifecycle and place relevant consequences near the operation |

Borrow the decision, not another project's identity, slogans, screenshots,
benchmarks or ecosystem-specific commands. A large project's sponsorship area
or long contents list is not automatically useful to a small repository.

## Documentation foundations

[GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
establishes the role of the project entry point, repository-relative links and
heading navigation. It also documents README discovery: `.github`, repository
root, then `docs`. Check for a competing surfaced file before assuming a root
rewrite is what visitors see.

[Diátaxis](https://diataxis.fr/) separates learning, task completion, reference
and explanation. Apply that distinction to decide what belongs inline and what
should be linked. It does not require creating four directories or turning the
README into a complete documentation site.
