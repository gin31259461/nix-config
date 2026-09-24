# Local AI service

The AI capability runs declared GGUF models with a pinned native llama.cpp build behind llama-swap. Nix generates the public router, Caddy and systemd policy; the Arch adapter checks prepared assets, ownership and service state before applying it. Compiled binaries and models remain outside the Nix store under their declared native locations.

```text
Tailnet HTTPS → Tailscale Serve → loopback Caddy → loopback llama-swap → loopback llama-server
```

Caddy forwards only `/health` and `/v1/*`. Management endpoints are not published. The model, profile, revision and checksum inventories belong to the AI module's Nix declarations.

## Prepare outside deployment

```bash
just prepare-ai          # Build and verify every declared asset.
just prepare-ai build    # Prepare the pinned llama.cpp build.
just prepare-ai model    # Download and fully verify declared models.
```

Preparation uses the declared llama.cpp source revision and reviewed build patch, installs the binary under a revision directory and atomically updates the `current` selector. Model downloads stage by declared identity, pass full SHA-256 verification and publish atomically. A root-owned receipt records each verified model. Routine deployment compares its identity and file metadata without hashing the entire GGUF on every run; `just prepare-ai model` performs explicit full verification and refreshes matching receipts. Unknown staging state, mismatched selectors and checksums require operator review. The build needs the native C++/ROCm/Vulkan toolchain.

## Deploy and inspect

```bash
just arch-workstation
curl --fail http://127.0.0.1:11434/v1/models
curl --fail http://127.0.0.1:11435/v1/models
sudo tailscale serve status --json
systemctl status llama-swap.service caddy.service
```

If the build selector has never been prepared, workstation deployment highlights an optional AI skip and leaves its files and services alone. Once the selector exists, a missing model, invalid build or model receipt, changed checksum, unmanaged Caddy policy, service failure or readiness change after preflight stops the run. Prepared assets are verified before services converge. Use `just arch-workstation verbose` for native command diagnostics.

Disabling AI withdraws convergence; it does not remove prepared binaries, models, native files, pending markers or Tailscale routes. The AI capability also declares client tools and skill presets through its public option interface; inspect [configuration](configuration.md) and the owning module for the current switches. [Deployment](deployment.md) describes shared progress and recovery.
