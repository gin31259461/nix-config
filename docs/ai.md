# Local AI service

The AI capability runs declared GGUF models with a pinned native llama.cpp build behind llama-swap. Nix generates the public router, Caddy and systemd policy; the Arch adapter checks prepared assets, ownership and service state before applying it. Compiled binaries and models remain outside the Nix store under their declared native locations.

```text
Tailnet HTTPS → Tailscale Serve → loopback Caddy → loopback llama-swap → loopback llama-server
```

Caddy forwards only `/health` and `/v1/*`. Management endpoints are not published. The model, profile, revision and checksum inventories belong to the AI module's Nix declarations.

## Select resident models

`programs.ai.llama.model.name` selects the default agent. An empty `llama.models`
keeps the legacy single-model behavior. With explicit entries, enable every
desired model, including `model.name`:

```nix
programs.ai.llama = {
  model.name = "qwen3.5-4b-q4-k-m";
  concurrentModels = true;
  maxLoadedModels = 2;
  memoryBudgetMiB = 11264;
  models = {
    "qwen3.5-4b-q4-k-m" = {
      enable = true;
      contextSize = 16384;
      fit = false;
      gpuLayers = 99;
      vramEstimateMiB = 6144;
    };
    "qwen2.5-coder-3b-q4-k-m" = {
      enable = true;
      contextSize = 4096;
      vramEstimateMiB = 3072;
    };
  };
};
```

Each model has independent device, context, cache, batch, parallel-slot and
offload settings. The agent inherits legacy `llama.model` overrides before
per-model overrides. Profiles share a model process and control request
sampling/thinking. They cannot change backend allocation. Unknown fields,
unselected profile targets, invalid batches and conflicting thinking flags fail
evaluation.

With concurrency enabled, selected count must not exceed `maxLoadedModels`.
Backends load on their first request and stay resident without idle eviction;
requests can execute simultaneously. Raising the limit alone does not start
models. With concurrency disabled, the limit must be one and models swap on
demand. Preparation covers selected models only; deselection leaves assets intact.

`vramEstimateMiB` and `memoryBudgetMiB` describe a measured operating budget.
Every selected model needs an estimate when a budget is set, and their sum must
fit. These fields do not constrain the allocator. `--fit-target` is a free-memory
margin, not an allocation ceiling. Fixed offload/context/batches with `fit = false`
avoid load-order-dependent fitting. Measure prompt-processing peaks, reserve
desktop/Sunshine headroom, and retest after model or runtime changes.

The legacy `qwen3.6-35b-a3b-ud-q5-k-m` option name remains for compatibility;
its actual file is MXFP4_MOE. Thinking profile suffixes remain available for the
selected agent. Inspect `/v1/models` for exact API IDs.

## Agent skills

Home Manager installs the explicitly selected skills into `~/.agents/skills`
and `~/.gemini/config/skills` as complete directory links. Enablement follows
`programs.ai.enable`, `programs.ai.skillsPresets.enable` for the shared agent
directory, and `programs.ai.agy.enable` plus `programs.ai.agy.skills.enable` for
the Antigravity directory. These switches are independent of llama.cpp asset
preparation. The source and selection registry lives in
[`modules/ai/skills.nix`](../modules/ai/skills.nix).

The `matt-pocock-skills` flake input owns Matt's skill content, including bundled
references, scripts and agent metadata. The `vercel-skills` input owns
`find-skills`. Both revisions are fixed in `flake.lock`. The six custom skills
remain in this repository, with their agent-specific content preserved.
Deployment uses the sources already captured by the built Home Manager
activation package; it does not run `npx`, download skills during activation,
or maintain the Skills CLI's runtime lock file.

Deploy the selected revisions with the normal workstation command:

```bash
just arch-workstation
```

Update only the skill sources, review the changed revisions and upstream
changes, then validate the resulting generation:

```bash
nix flake update matt-pocock-skills vercel-skills
just check-fast
just check
just build
nix build --no-link --show-trace --print-build-logs \
  '.#homeConfigurations."abnertu@arch".activationPackage'
git diff --check
```

Either input can be updated on its own. After review and successful checks,
run `just arch-workstation` to activate the new version and commit the reviewed
lock change. `just arch-workstation update` controls native package convergence;
it does not advance skill source revisions. To undo an update, restore the
reviewed earlier lock entries, rebuild and redeploy. Source checks do not perform
live activation.

Adding a skill requires an explicit registry change. A selected upstream path
that disappears or loses its `SKILL.md` fails evaluation, so source updates
cannot silently drop selected skills. Local modifications to upstream skills
are replaced by the upstream version during this migration; make intentional
custom forks separately owned before editing installed content. Home Manager
handles the old links it previously owned during activation and reports
unmanaged file collisions rather than overwriting them. No custom directory
cleanup or backup operation is added.

This migration retires `batch-grill-me`, `design-an-interface`, `edit-article`,
`qa`, `request-refactor-plan`, `resolving-merge-conflicts`,
`ubiquitous-language` and `writing-great-skills`, which no longer exist under
those names upstream. The confirmed rename `writing-great-skills` is replaced
by `writing-for-agents`; other newly introduced skills are not automatically
selected. See the [upstream changelog](https://github.com/mattpocock/skills/blob/main/CHANGELOG.md).

The [Matt installation guide](https://github.com/mattpocock/skills#installation-30-second-setup)
also supports installing through the
[Skills CLI](https://github.com/vercel-labs/skills). That CLI is provided by
`vercel-labs/skills`, not by Matt's repository. Its optional interactive
`find-skills` prompt is skipped with `--yes` or noninteractive input; this
configuration selects that skill explicitly. Use Nix input updates for these
Home Manager-owned skills; do not use `npx skills update` to overwrite their
installed links. Run `setup-matt-pocock-skills` separately for each project when
you want its project-specific workflow configuration.

Antigravity's [official skill guide](https://antigravity.google/docs/skills)
documents `~/.gemini/config/skills` for its IDE/global configuration. This
preserves the existing projection; Gemini CLI and Antigravity CLI have separate
agent-specific directories and are not additional targets of this migration.

## Codex local profile

When AI, Codex and llama.cpp are enabled, Home Manager writes
`~/.codex/llama-cpp.config.toml` from the selected default agent's API ID and
effective context size. The file defines a `llama_cpp` Responses API provider at
`http://127.0.0.1:11434/v1`, disables web search for this profile and sets
automatic compaction at 75% of the context window. With the default 16K agent,
Codex compacts at 12K tokens, leaving about 4K tokens for the active turn; this
is a compaction trigger, not a hard output limit. A model or context change is
reflected when the next Home Manager generation is activated.

The local profile disables Codex multi-agent tools. Codex 0.160 enables the
`multi_agent_v1` namespace by default, while this pinned llama.cpp Responses
converter only supports function tools. Ordinary function tools and shell use
remain available in this profile; multi-agent behavior in other Codex profiles
is unchanged.

Select the generated profile with `codex --profile llama-cpp` or
`codex exec --profile llama-cpp "your task"`. Standalone profiles require
[Codex 0.134 or newer](https://learn.chatgpt.com/docs/config-file/config-advanced);
profile loading, streaming and a shell-tool round trip
were verified with Codex 0.160.0 against a disposable synthetic backend.
The Qwen3.5 template correction was also verified with the actual prepared
4B GGUF and native llama.cpp: a streamed reply and a `pwd` tool round trip
both completed through the Responses API using an isolated Codex home.
Prepare the AI assets and converge the native service before using the profile.

Qwen3.5 uses a managed chat template that preserves multiple system/developer
instructions in conversation order, including instruction updates after user
messages. Its original tool and thinking formats remain intact. The embedded
GGUF template rejects these Codex instructions with HTTP 500 (`System message
must be at the beginning`), which Codex may display as a generic high-demand
error. Redeploy after a template update; the model does not need downloading
or rebuilding.

`--profile` uses the profile file under the default `~/.codex` directory; a custom `CODEX_HOME` uses its own Codex home and
does not read this generated file. Set `programs.ai.codex.localProfile.enable =
false` to stop managing it. The profile file is an independent Home Manager
file; the module does not own or rewrite `~/.codex/config.toml`, credentials,
permissions or other Codex settings. Resolve an existing file collision before
activating Home Manager.

## FIM completion

Use base completion weights through `/v1/completions`, with raw prefix/suffix
tokens rather than chat messages:

```bash
curl --fail http://127.0.0.1:11434/v1/completions \
  -H 'Content-Type: application/json' \
  --data '{"model":"Qwen2.5-Coder-3B-Q4_K_M.gguf","prompt":"<|fim_prefix|>def add(a, b):\n    <|fim_suffix|>\n\nassert add(2, 3) == 5\n<|fim_middle|>","max_tokens":64,"temperature":0,"stop":["<|fim_pad|>","<|endoftext|>","<|im_end|>"]}'
```

Both completion candidates contain these FIM tokens. Stop strings are explicit
because their GGUF EOS declarations differ. Embedded generic chat templates do
not make base weights instruction-tuned. Configure editor plugins with a
separate completion ID and the prefix/suffix format. Include a file/language
context in the prefix (for example `# Nix expression`) when syntax is ambiguous.
The agent default has 16K total context; configure the harness to compact before
that prompt-plus-output limit. A larger context needs fresh speed measurements.

## Measure locally

These opt-in tools perform live GPU work, separate from deployment and flake
checks. Download candidates to scratch at declared revisions and verify SHA-256.
Avoid a duplicate large agent alongside the managed router. For isolated tests,
stop the router during an agreed window and restore it afterwards without
changing `/etc`, receipts or the prepared selector.

Identify the dedicated GPU's sysfs path rather than assuming `card0`:

```bash
for device in /sys/class/drm/card[0-9]/device; do
  test ! -f "$device/mem_info_vram_total" || {
    printf '%s\n' "$device"
    cat "$device/mem_info_vram_total" "$device/mem_info_vram_used"
  }
done
python modules/ai/benchmark.py \
  --model /path/to/verified-model.gguf \
  --binary-prefix /opt/llama-cpp-opencode/current \
  --device-path /sys/class/drm/card1/device \
  --devices ROCm0,Vulkan0 --batches 2048 --ubatches 64,512 \
  --caches q8_0,q4_0 --threads 8 --gpu-layers 99 \
  --min-free-mib 4096 --output /var/tmp/ai-bench.json
```

The sequential matrix records PP512/PP4096/TG128 with three native repetitions,
binary revision, model checksum, arguments, raw diagnostics and sampled VRAM
peaks. Add `--depths 8192` to measure generation after a longer prefix. The
reserve monitor terminates its own test process on a breach or timeout; polling
cannot prevent transient allocations and is not a hard cap.

```bash
python modules/ai/probe.py --base-url http://127.0.0.1:11434 \
  --model MODEL_ID --thinking-model MODEL_ID:thinking-coding \
  --output /var/tmp/ai-chat.json
python modules/ai/probe.py --base-url http://127.0.0.1:11434 \
  --model COMPLETION_ID --mode fim --output /var/tmp/ai-fim.json
```

Probes use synthetic prompts, compare thinking off/on, and repeat prefixes to
expose cache reuse. They separate first SSE event, reasoning and visible answer,
and retain failures/partial output. Router aliases can enforce their declared
thinking flag; use `--thinking-model` to compare the matching thinking alias
against the default model. A token limit can end thinking before the
final answer. Never infer long-context speed from empty-context TG128.

Agent latency includes loading, queueing, prompt ingestion, reasoning and visible
generation. Stable prefixes help cache reuse. MTP accelerates decoding, requires
MTP tensors and adds memory; the pinned Qwen3.6 MXFP4 artifact has none. Test MTP
only when decoding is the bottleneck and the shared budget permits it. Upstream
[HIP PP regression #18823](https://github.com/ggml-org/llama.cpp/issues/18823) and
[MTP reservation #26038](https://github.com/ggml-org/llama.cpp/issues/26038) are
diagnostic leads, not proof that this machine has those bugs.

See [local measurements](ai-benchmarks.md) for hardware, chosen parameters and
limits. Test simultaneous residency and requests during actual Sunshine
streaming before claiming remote-streaming performance is verified.

## Prepare outside deployment

```bash
just prepare-ai          # Build and verify every declared asset.
just prepare-ai build    # Prepare the pinned llama.cpp build.
just prepare-ai model    # Download and fully verify declared models.
```

Preparation uses the declared llama.cpp source revision and reviewed build patch, installs the binary under a revision directory and atomically updates the `current` selector. Model downloads stage by declared identity, pass full SHA-256 verification and publish atomically. A root-owned receipt records each verified model. Routine deployment compares its identity and file metadata without hashing the entire GGUF on every run; `just prepare-ai model` performs explicit full verification and refreshes matching receipts. Unknown staging state, mismatched selectors and checksums require operator review. The build needs the native C++/ROCm/Vulkan toolchain.

Downloads use `hf download --local-dir` without `--cache-dir`; local-directory
metadata stays inside the owned download stage. If a download fails, rerun
`just prepare-ai model`: a stage with the same declared identity is reused,
then the completed GGUF must pass SHA-256 verification before publication.
A stage belonging to a different declaration still requires operator review.
See the [Hugging Face download guide](https://huggingface.co/docs/huggingface_hub/guides/download).

## Deploy and inspect

```bash
just arch-workstation
curl --fail http://127.0.0.1:11434/v1/models
curl --fail http://127.0.0.1:11435/v1/models
sudo tailscale serve status --json
systemctl status llama-swap.service caddy.service
```

If the build selector has never been prepared, workstation deployment highlights an optional AI skip and leaves its files and services alone. Once the selector exists, a missing model, invalid build or model receipt, changed checksum, unmanaged Caddy policy, service failure or readiness change after preflight stops the run. Prepared assets are verified before services converge. Use `just arch-workstation verbose` for native command diagnostics.

The retired standalone `llama-server` preset and drop-in are recognized against
fixed historical policy, independently of the current selected models and
residency limit. Exact known files may remain in place during migration to
llama-swap; deployment stops/disables the old service if necessary. Modified
presets, drop-ins and manual local overrides still require explicit adoption.
No legacy files or model assets are automatically removed.

Disabling AI withdraws convergence; it does not remove prepared binaries, models, native files, pending markers or Tailscale routes. The AI capability also declares client tools and skill presets through its public option interface; inspect [configuration](configuration.md) and the owning module for the current switches. [Deployment](deployment.md) describes shared progress and recovery.
