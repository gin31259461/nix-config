{
  pkgs,
  config,
}:
let
  enabled = config.enable;
  settings = pkgs.writeText "searxng-settings.yml" ''
    use_default_settings:
      engines:
        keep_only: [google, bing]
    engines:
      - name: google
        disabled: false
        weight: 2
      - name: bing
        disabled: false
    search:
      safe_search: 1
      formats: [html, json]
    server:
      bind_address: "127.0.0.1"
      port: ${toString config.port}
      limiter: false
      public_instance: false
  '';
  start = pkgs.writeShellScript "searxng-start" ''
    set -eu
    secret_file="$STATE_DIRECTORY/secret"
    if [ ! -s "$secret_file" ]; then
      umask 077
      ${pkgs.openssl}/bin/openssl rand -hex 32 > "$secret_file"
    fi
    export SEARXNG_SECRET="$(${pkgs.coreutils}/bin/cat "$secret_file")"
    export SEARXNG_SETTINGS_PATH=${settings}
    exec ${pkgs.searxng}/bin/searxng-run
  '';
  unit = ''
    [Unit]
    Description=SearXNG Metasearch Engine
    After=network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    DynamicUser=true
    StateDirectory=searxng
    ExecStart=${start}
    Restart=on-failure
    RestartSec=5
    NoNewPrivileges=true
    PrivateTmp=true
    ProtectSystem=strict
    ProtectHome=true

    [Install]
    WantedBy=multi-user.target
  '';
in
{
  manifest = pkgs.writeText "arch-searxng.json" (
    builtins.toJSON {
      inherit enabled unit;
      endpoint = "http://127.0.0.1:${toString config.port}";
      curl = "${pkgs.curl}/bin/curl";
      unitPath = "/etc/systemd/system/searxng.service";
      receipt = "/var/lib/nix-config/arch/searxng.ready";
      pending = "/var/lib/nix-config/arch/searxng.pending";
    }
  );
}
