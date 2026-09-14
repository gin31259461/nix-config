# Personal Agent

The Personal Agent application is built from the pinned `personal-agent` flake
input. This repository owns its Arch account, runtime directories and systemd
unit; the application repository owns Python dependencies and behavior.

The Host enables the capability with `services.personalAgent.enable`. Runtime
configuration remains outside Git and the Nix store:

```text
/etc/personal-agent/config.toml
/etc/personal-agent/agent.env
/var/lib/personal-agent/agent.db
```

`config.toml` contains Discord identities, Notion mappings and inference settings.
`agent.env` contains exactly `DISCORD_TOKEN` and `NOTION_TOKEN`. The configuration
file must be owned by `root:personal-agent` with mode `0640`; the environment file
must be `root:root` with mode `0600`. Deployment validates both without printing
their values.

An enabled module with no prior configuration is reported as an optional
`not ready` skip. After a successful deployment, missing or unsafe configuration
is runtime drift and stops deployment.

The service runs the exact package fixed by `flake.lock`; deployment never creates
a virtual environment or resolves Python packages. Application upgrades are
intentional input updates:

```bash
nix flake update personal-agent
just check
just build
```

Inspect the deployed service after activation:

```bash
sudo systemctl status personal-agent.service
sudo journalctl -u personal-agent.service -f
```

Disabling the declaration withdraws management without stopping the service or
deleting its account, configuration or state. Explicit workstation purge removes
the managed unit and stops the service while preserving those runtime files and
the account.
