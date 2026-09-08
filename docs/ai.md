# Operate local AI services

The AI Module selects native Ollama and, on AMD Hosts, its Vulkan backend. Its
optional proxy exposes only Caddy through Tailscale Serve:

```text
Tailnet HTTPS → Tailscale Serve → 127.0.0.1:11435 Caddy
                                → 127.0.0.1:11434 Ollama
```

Ollama and Caddy remain loopback-only. Tailscale access policy determines which
tailnet peers can reach the API; this configuration does not add application
authentication, Funnel exposure, or LAN firewall rules.

## Select a Vulkan device

The supplied AMD Host selects Vulkan device `0`:

```nix
programs.ai.ollama.vulkan.visibleDevices = [ 0 ];
```

Treat this as a reviewed Host value. Ollama accepts numeric Vulkan IDs, and its
enumeration can differ from another Vulkan inventory tool. Before first
deployment, identify the intended device using the installed Ollama backend's
`VulkanN` diagnostics and corroborate its name and PCI identity with
`vulkaninfo --summary`. Do not substitute a PCI address, DRM node or ROCm ID.
Override the list in [configuration.nix](../configuration.nix) if the intended
device has another Ollama ID. Missing, empty, duplicate and negative selections
are rejected before mutation. Recheck after driver or backend changes.

Ollama's [GPU documentation](https://docs.ollama.com/gpu) defines numeric Vulkan
selection. Its [discovery implementation](https://github.com/ollama/ollama/blob/main/discover/llama_server.go)
documents why inventories cannot be assumed to share an ordinal.

The managed `/etc/ollama-vulkan.conf` contains `OLLAMA_VULKAN=1`, the reviewed
`GGML_VK_VISIBLE_DEVICES` list, and `OLLAMA_KEEP_ALIVE=-1`. A dedicated native
unit drop-in loads the file, binds Ollama to `127.0.0.1:11434`, and gives only
the `ollama` service supplementary `render` access. Negative keep-alive retains
loaded models in memory; an API request can override it. See the
[Ollama server FAQ](https://docs.ollama.com/faq).

## Prepare Caddy and Tailscale Serve

The Arch Caddy package supplies the expected Unix admin endpoint and `conf.d`
import. The first deployment accepts an empty file, the recognized Arch package
template, or an already adopted Caddyfile with the same admin endpoint and
import. Any custom or conflicting main file stops before adoption. The package
welcome site is removed when its exact template is adopted, so this capability
does not expose port 80.

Caddy's package tmpfiles rule prepares `/run/caddy` as `0750 caddy:caddy`; Caddy
creates `/run/caddy/admin.socket`. Deployment validates the complete config,
starts or repairs the native service, verifies the path is a Unix socket, and
requires reload through its explicit address to succeed. It then checks Ollama
through `127.0.0.1:11435`.

Before enabling the remote route, sign the machine into Tailscale and enable the
tailnet prerequisites for Serve HTTPS. Review existing port 443 routes and
Funnel state. The controller only adopts an empty Serve configuration or its
own exact route; it never resets unrelated Serve state, invokes `tailscale up`,
or handles authentication material. The persistent route is equivalent to:

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:11435
```

Tailscale documents [Serve configuration and persistence](https://tailscale.com/docs/reference/tailscale-cli/serve).

## Deploy and verify

New native packages require the explicit update path:

```bash
nix run .#arch-workstation -- --update
```

The controller installs `ollama`, `ollama-vulkan` and `caddy`, then converges
Ollama before Caddy and publishes Serve only after both loopback checks pass.
Interrupted actions retain private pending markers and retry on the next run.
A healthy repeat avoids file replacement, service restart, Caddy reload and
Serve publication.

After deployment, verify a suitable model rather than downloading one as part
of activation:

```bash
ollama ps
curl --fail http://127.0.0.1:11434/api/version
curl --fail http://127.0.0.1:11435/api/version
sudo test -S /run/caddy/admin.socket
sudo caddy reload \
  --config /etc/caddy/Caddyfile \
  --address unix//run/caddy/admin.socket
sudo tailscale serve status --json
```

Confirm the model's processor allocation, streaming responses through both
proxy hops, the intended tailnet peer's HTTPS access and denial for peers outside
the tailnet policy. Reboot once and verify native services and the background
Serve route return.

Setting an enable option to false withdraws desired contributions only. It does
not stop an existing service, remove a package or file, delete models, clear a
pending action, or retire an existing Serve route. Retiring deployed state is a
separate, explicitly scoped operator action.
