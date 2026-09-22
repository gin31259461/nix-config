# AI service

The AI module runs declared GGUF models through a pinned llama.cpp build and the
llama-swap router. The current inventory contains one model with multiple
requestable inference profiles. llama-swap, llama-server, and Caddy listen only
on loopback. Tailscale Serve publishes the Caddy listener securely to the tailnet.

```text
Tailnet HTTPS -> Tailscale Serve -> 127.0.0.1:11435 Caddy
                                  -> 127.0.0.1:11434 llama-swap
                                  -> 127.0.0.1:<dynamic> llama-server
```

Source revision, build policy, model revisions, checksums, and runtime defaults
are owned by the AI artifact inventory. Models remain under
`/var/lib/llama/models` and never enter the Nix store. Host-owned profiles expose
the current model as the base ID plus `:thinking-general`, `:thinking-coding`,
`:instruct`, and `:preserved-thinking` aliases.

## Prepare

AI native assets are intentionally outside routine workstation deployment.
Prepare them explicitly:

```bash
just prepare-ai
just prepare-ai build
just prepare-ai model
```

Equivalent direct commands:

```bash
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare -- --build-only
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare -- --model-only
```

Preparation builds the pinned llama.cpp revision, applies the reviewed grammar
threshold change, installs it under the declared revision directory, atomically
updates the `current` selector, and downloads every declared GGUF with the
Nix-provided Hugging Face `hf download` command. Each model is downloaded into
an identity-checked staging directory, verified with its declared SHA-256, and
published atomically. An interrupted download can be retried for the same
declaration; an unknown or mismatched staging directory requires operator
review. The build requires the native C++/ROCm/Vulkan development toolchain.

After full SHA-256 verification, preparation writes a root-owned receipt beside
each model. Routine deployment compares that receipt with the declared artifact
and the model's device, inode, size, and timestamps. It therefore detects model
replacement or modification without rereading the complete GGUF on every run.
Run `just prepare-ai model` to perform an explicit full checksum verification and
refresh matching receipts.

Preparation reports tasks for the selected build/model mode, including source
preparation, compilation, checksum verification, and publication. Existing assets
are reported as checked rather than downloaded or rebuilt. A download finishing
does not mark preparation complete: checksum verification and receipt publication
must succeed first. Git, Ninja, and Hugging Face retain their native output while
the shared task display yields the terminal; completed task results remain in
the console history. See [progress display](deployment.md#progress-display) for
plain-output modes and terminal behavior.

Preparation is idempotent for matching owned state. An existing conflicting
revision, selector, staging path, or model checksum is an error and requires
operator review.

## Deployment behavior

When AI is enabled but the build or one of its declared models has not been prepared,
workstation deployment prints a highlighted skip message (plain text in log mode) and continues without
touching AI files or services:

```text
SKIP optional module ai: llama.cpp build/model is not prepared; run 'just prepare-ai'
```

This skip is strictly limited to the explicit `not ready` adapter status. A mismatched
selector, invalid receipt, unmanaged Caddy ownership, invalid service state, or
native command failure stops deployment.

After preparation, normal deployment writes the llama-swap JSON/YAML config and
service unit, converges the router, validates Caddy, checks the local model
listing endpoint, and reconciles the declared Tailscale Serve route. Caddy only
proxies `/health` and `/v1/*`; llama-swap management endpoints are never exposed
through the published listener.

```bash
just arch-workstation
```

## Verify

```bash
curl --fail http://127.0.0.1:11434/v1/models
curl --fail http://127.0.0.1:11435/v1/models
sudo tailscale serve status --json
systemctl status llama-swap.service caddy.service
```

For command-level diagnostics, use:

```bash
just arch-workstation verbose
```

The privileged adapter prints each native command and its complete captured
stdout/stderr. Without verbose mode, failed native commands still report both
streams.

Disabling `programs.ai.llama.enable` withdraws AI convergence. It does not delete
prepared binaries, models, system files, pending markers, or Tailscale routes.

## Client tools and skills

The AI module also declares companion client tools and skill presets:

* `programs.ai.codex.enable`: manages the AUR `openai-codex-bin` package.
* `programs.ai.agy.enable`: master toggle for Antigravity (agy) tools.
* `programs.ai.agy.pkg.enable`: manages the AUR `antigravity-cli` package.
* `programs.ai.agy.skills.enable`: projects `.gemini/config/skills/*` into `~/.gemini/config/skills/`.
* `programs.ai.skillsPresets.enable`: projects `.agents/skills/*` into `~/.agents/skills/`.
