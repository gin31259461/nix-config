# AI service

The AI module runs one reviewed GGUF model through a pinned llama.cpp build. Both
llama-server and Caddy listen only on loopback. Tailscale Serve publishes the
Caddy listener to the tailnet.

```text
Tailnet HTTPS -> Tailscale Serve -> 127.0.0.1:11435 Caddy
                                  -> 127.0.0.1:11434 llama-server
```

Source revision, build policy, model revision, checksum and runtime defaults are
owned by `modules/ai/artifacts.nix`. The selected model remains under
`/var/lib/llama/models` and never enters the Nix store.

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
sudo nix run .#llama-prepare
sudo nix run .#llama-prepare -- --build-only
sudo nix run .#llama-prepare -- --model-only
```

Preparation builds the pinned llama.cpp revision, applies the reviewed grammar
threshold change, installs it under the declared revision directory, atomically
updates the `current` selector, downloads the selected GGUF and verifies its
SHA-256. It requires the native C++/ROCm/Vulkan development toolchain.

Preparation is idempotent for matching owned state. An existing conflicting
revision, selector, staging path or model checksum is an error and requires
operator review.

## Deployment behavior

When AI is enabled but the build or model has not been prepared, workstation
deployment prints a bold yellow skip message and continues without touching AI
files or services:

```text
SKIP optional module ai: llama.cpp build/model is not prepared; run 'just prepare-ai'
```

This skip is limited to the explicit `not ready` adapter status. A mismatched
selector, invalid receipt, unmanaged Caddy ownership, invalid service state or
native command failure still stops deployment.

After preparation, normal deployment writes the llama-server preset and systemd
drop-in, converges the service, validates Caddy, checks the local model endpoint
and reconciles the declared Tailscale Serve route.

```bash
just arch-workstation
```

## Verify

```bash
curl --fail http://127.0.0.1:11434/v1/models
curl --fail http://127.0.0.1:11435/v1/models
sudo tailscale serve status --json
systemctl status llama-server.service caddy.service
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
