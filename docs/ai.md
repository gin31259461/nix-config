# llama.cpp service

The AI Module selects one llama.cpp model from a reviewed inventory. The server and Caddy bind to
loopback; Tailscale Serve publishes only the Caddy listener:

```text
Tailnet HTTPS → Tailscale Serve → 127.0.0.1:11435 Caddy
                                → 127.0.0.1:11434 llama-server
```

The AI Module privately pins llama.cpp commit
`434ddbbc0e30522e897670681e503b797c12b7c1`, raises the grammar repetition
threshold from 2,000 to 20,000 with a source guard, and owns the immutable
Hugging Face revision and SHA-256 for each external GGUF. Each inventory entry
also owns its tested runtime preset. The Host selects
`programs.ai.llama.model.name` and may override runtime choices such as the
device and context size; it does not declare download integrity data. Add
another reviewed entry to `modules/ai/artifacts.nix` before selecting a
different model. Models remain under `/var/lib/llama/models`; they never enter
the Nix store.

## Prepare native assets

Preparation is a separate operator action:

```bash
sudo nix run .#llama-prepare
```

Use `--build-only` or `--model-only` to limit the action. It checks out the
exact source revision, refuses to patch an unexpected grammar source line,
builds Release HIP and Vulkan backends into a revision-specific directory under
`/opt/llama-cpp-opencode`, atomically selects it through `current`, downloads the model from its pinned repository
revision, and verifies its SHA-256 before installation. A protected system lock
serializes preparation; existing unowned revision, selector, staging, or model
paths stop the command for operator recovery. This command requires the native
ROCm and Vulkan development toolchain and administrator access.
It does not update pacman, alter repositories, or start services.
Build scratch data uses private storage under `/var/tmp`; model downloads stage
beside the final model so they do not require a second 21 GB filesystem copy.
On a fresh Arch installation, prepare the native compiler/backend prerequisites
explicitly with `base-devel`, `rocm-hip-sdk`, and `vulkan-headers`. Nix supplies
the controller's CMake, Git, Ninja, curl, and basic command-line tools.

Routine `arch-switch` deploys AI only when the prepared executable, build
receipt, and selected model are all present. If preparation has not completed,
it prints an AI skip message and continues the rest of the deployment without
writing AI files or touching AI services. A present but mismatched build receipt
still stops AI convergence because that is initialized-state drift requiring
operator review. Native llama.cpp/Caddy packages and build dependencies belong
to the explicit preparation workflow and are not hard prerequisites for routine
deployment.

Before the first source-managed deployment, preserve and move the manual
`60-local.conf` drop-in and the legacy `nix-config-ollama.caddy` site out of
their systemd/Caddy directories. Preflight rejects either legacy path before
writing anything, so the operator can review and restore those files if needed.

## Deploy and verify

```bash
nix run .#arch-workstation
curl --fail http://127.0.0.1:11434/v1/models
curl --fail http://127.0.0.1:11435/v1/models
sudo tailscale serve status --json
```

Deployment writes `/etc/llama/server/models.ini` and the
`llama-server.service` drop-in. The declared preset contains only the selected
inventory model. The current inventory defaults to
`qwen3.5-35b-a3b-mxfp4`; code completion is not declared.
It also adopts only the known Arch Caddy template, preserves a compatible
existing wildcard-import Caddyfile, and rejects unrelated Caddy or Serve
configuration. Pending markers retain interrupted service, reload, and
publication actions for the next run.

Setting `programs.ai.llama.enable = false` withdraws all llama.cpp
contributions. It does not delete the executable, model, service files, Caddy
site, pending markers, or Serve routes.
