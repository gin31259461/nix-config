{
  pkgs,
  package,
  enabled,
}:
let
  unit = ''
    [Unit]
    Description=Personal Agent
    After=network-online.target llama-swap.service
    Wants=network-online.target
    Requires=llama-swap.service

    [Service]
    Type=simple
    User=personal-agent
    Group=personal-agent
    EnvironmentFile=/etc/personal-agent/agent.env
    ExecStart=${package}/bin/personal-agent run --config /etc/personal-agent/config.toml
    Restart=on-failure
    RestartSec=5
    StateDirectory=personal-agent
    NoNewPrivileges=true
    PrivateTmp=true
    ProtectSystem=strict
    ProtectHome=true

    [Install]
    WantedBy=multi-user.target
  '';
in
{
  manifest = pkgs.writeText "arch-personal-agent.json" (
    builtins.toJSON {
      inherit enabled unit;
      executable = "${package}/bin/personal-agent";
      config = "/etc/personal-agent/config.toml";
      secrets = "/etc/personal-agent/agent.env";
      state = "/var/lib/personal-agent";
      unitPath = "/etc/systemd/system/personal-agent.service";
      receipt = "/var/lib/nix-config/arch/personal-agent.ready";
      pending = "/var/lib/nix-config/arch/personal-agent.pending";
    }
  );
}
