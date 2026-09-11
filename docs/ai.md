# AI service

The AI module runs declared GGUF models through a pinned llama.cpp build and the
llama-swap router. The current inventory contains one model with multiple
requestable inference profiles. llama-swap, llama-server and Caddy listen only
on loopback. Tailscale Serve publishes the Caddy listener to the tailnet.

```text
Tailnet HTTPS -> Tailscale Serve -> 127.0.0.1:11435 Caddy
                                  -> 127.0.0.1:11434 llama-swap
                                  -> 127.0.0.1:<dynamic> llama-server
```

Source revision, build policy, model revisions, checksums and runtime defaults
are owned by the AI artifact inventory. Models remain under
`/var/lib/llama/models` and never enter the Nix store. Host-owned profiles expose
the current model as the base ID plus `:thinking-general`, `:thinking-coding`,
`:instruct` and `:preserved-thinking` aliases.

## Prepare

AI native assets are intentionally outside routine workstation deployment.
Prepare them explicitly:

```bash
just prepare-ai
just prepare-ai build
just prepare-ai model
```

Equivalent direct commands are:

```bash
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare -- --build-only
sudo nix --extra-experimental-features 'nix-command flakes' run .#llama-prepare -- --model-only
```

Preparation builds the pinned llama.cpp revision, applies the reviewed grammar
threshold change, installs it under the declared revision directory, atomically
updates the `current` selector, downloads every declared GGUF and verifies each
SHA-256. It requires the native C++/ROCm/Vulkan development toolchain.

Preparation is idempotent for matching owned state. An existing conflicting
revision, selector, staging path or model checksum is an error and requires
operator review.

## Deployment behavior

When AI is enabled but the build or one of its declared models has not been prepared, workstation
deployment prints a bold yellow skip message and continues without touching AI
files or services:

```text
SKIP optional module ai: llama.cpp build/model is not prepared; run 'just prepare-ai'
```

This skip is limited to the explicit `not ready` adapter status. A mismatched
selector, invalid receipt, unmanaged Caddy ownership, invalid service state or
native command failure still stops deployment.

After preparation, normal deployment writes the llama-swap JSON/YAML config and
service unit, converges the router, validates Caddy, checks the local model
listing endpoint and reconciles the declared Tailscale Serve route. Caddy only
proxies `/health` and `/v1/*`; llama-swap management endpoints are not exposed
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

For command-level diagnostics use:

```bash
just arch-workstation verbose
```

The privileged adapter prints each native command and its complete captured
stdout/stderr. Without verbose mode, failed native commands still report both
streams.

Disabling `programs.ai.llama.enable` withdraws AI convergence. It does not delete
prepared binaries, models, system files, pending markers or Tailscale routes.
