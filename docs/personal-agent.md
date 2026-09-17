# Personal Agent

The Personal Agent application is built from the pinned `personal-agent` flake
input. This repository owns its Arch account, runtime directories, and systemd
unit; the application repository owns Python dependencies and internal behavior.

The Host enables the capability with `services.personalAgent.enable`. Runtime
configuration remains outside Git and the Nix store:

```text
/etc/personal-agent/config.toml
/etc/personal-agent/agent.env
/var/lib/personal-agent/agent.db
```

`config.toml` contains Discord identities, Notion mappings, and inference settings.
`agent.env` contains sensitive secrets: `DISCORD_TOKEN` and `NOTION_TOKEN`.
The configuration file must be owned by `root:personal-agent` with mode `0640`;
the environment file must be owned by `root:root` with mode `0600`. Deployment
validates permissions and existence without printing secret values.

An enabled module with no prior configuration is reported as an optional
`not ready` skip. After a successful deployment, missing or unsafe configuration
is considered runtime drift and halts deployment.

The service runs the exact package fixed by `flake.lock`; deployment never creates
virtual environments or resolves Python packages at runtime. Application upgrades
are intentional flake input updates:

```bash
nix flake update personal-agent
just check
just build
```

## Service operations

Inspect the deployed service after activation:

```bash
sudo systemctl status personal-agent.service
sudo journalctl -u personal-agent.service -f
```

## Private web search with SearXNG

Enable private loopback web search declaratively:

```nix
services.searxng.enable = true;
services.personalAgent.searxng.enable = true;
```

- `services.searxng.enable`: Deploys the independent `searxng.service` metasearch engine
  daemon on `127.0.0.1:8888` using the default `pkgs.searxng` package with weighted Google
  results and Bing fallback. Its generated runtime secret remains under `/var/lib/searxng`.
- `services.personalAgent.searxng.enable`: Configures Personal Agent to use SearXNG by
  injecting `PERSONAL_AGENT_WEB_SEARCH_URL` (default `http://127.0.0.1:8888`) and adding
  systemd unit dependencies to local `searxng.service` when both are enabled.

## Disable and purge semantics

Disabling either declaration withdraws management without stopping running services or
deleting accounts, configuration files, or database state. Explicit workstation purge
(`just arch-workstation purge`) removes the managed unit and stops the service while
preserving all runtime data, configuration, and accounts.
