{
  pkgs,
  package,
  config,
}:
let
  enabled = config.enable;
  webSearch = config.webSearch.enable;
  endpoint = "http://127.0.0.1:${toString config.webSearch.port}";
  searxng = pkgs.searxng.overrideAttrs (_: {
    version = "0-unstable-2026-09-01";
    src = pkgs.fetchFromGitHub {
      owner = "searxng";
      repo = "searxng";
      rev = "79c8ffe0da5d75e48dbd55d505adab5d0ca554b9";
      hash = "sha256-lxxO1wcZ9RDnw/28mVaT4oGGWkw5yEaeagcCdnlEInI=";
    };
    preBuild = ''
      export SEARX_DEBUG="true"
      cat > searx/version_frozen.py <<EOF
      VERSION_STRING="2026.9.1+79c8ffe0"
      VERSION_TAG="2026.9.1+79c8ffe0"
      DOCKER_TAG="2026.9.1-79c8ffe0"
      GIT_URL="https://github.com/searxng/searxng"
      GIT_BRANCH="master"
      EOF
    '';
  });
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
      port: ${toString config.webSearch.port}
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
    exec ${searxng}/bin/searxng-run
  '';
  searxngUnit = ''
    [Unit]
    Description=Private SearXNG for Personal Agent
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
  unit = ''
    [Unit]
    Description=Personal Agent
    After=network-online.target llama-swap.service${if webSearch then " searxng.service" else ""}
    Wants=network-online.target
    Requires=llama-swap.service${if webSearch then " searxng.service" else ""}

    [Service]
    Type=simple
    User=personal-agent
    Group=personal-agent
    EnvironmentFile=/etc/personal-agent/agent.env
    ${if webSearch then "Environment=PERSONAL_AGENT_WEB_SEARCH_URL=${endpoint}" else ""}
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
      webSearch = {
        enable = webSearch;
        inherit endpoint searxngUnit;
        curl = "${pkgs.curl}/bin/curl";
        unitPath = "/etc/systemd/system/searxng.service";
        receipt = "/var/lib/nix-config/arch/searxng.ready";
      };
      receipt = "/var/lib/nix-config/arch/personal-agent.ready";
      pending = "/var/lib/nix-config/arch/personal-agent.pending";
    }
  );
}
