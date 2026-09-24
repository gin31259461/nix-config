# Personal Agent

This Host can enable the pinned `personal-agent` flake package through `services.personalAgent.enable`. The application repository owns Python dependencies and internal behavior. This repository owns its Arch account, native directories, public unit policy and service convergence. Nix generates the fixed unit; runtime configuration and database state stay outside Git and the Nix store.

The operator supplies `/etc/personal-agent/config.toml` and `/etc/personal-agent/agent.env` outside this repository. The former holds application identities and inference settings and must be `root:personal-agent` mode `0640`; the latter holds secret tokens and must be `root:root` mode `0600`. Database state stays under `/var/lib/personal-agent/`. Deployment validates the presence and metadata of these paths without printing values. Do not read or copy their contents into diagnostics.

An enabled module with no prior configuration may report an optional `not ready` skip. Once prepared, missing or unsafe configuration is runtime drift and stops deployment. If readiness changes after preflight, convergence stops rather than turning the change into a skip. Application updates are intentional flake input changes followed by source checks and a build:

```bash
nix flake update personal-agent
just check
just build
```

## Operate the service

```bash
sudo systemctl status personal-agent.service
sudo journalctl -u personal-agent.service -f
```

For private loopback web search, enable both the independent SearXNG service and the Agent integration:

```nix
services.searxng.enable = true;
services.personalAgent.searxng.enable = true;
```

SearXNG binds loopback; its generated runtime secret stays under its native state directory. The Agent integration supplies the local search URL and orders the services when both are enabled. Their current defaults belong to the owning modules.

Disabling either declaration withdraws management without deleting accounts, configuration or database state. Explicit workstation purge removes managed units and stops managed services while preserving that data and the accounts. See [deployment](deployment.md) for purge scope and failure recovery.
