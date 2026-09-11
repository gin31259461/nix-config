"""Converge Arch-owned llama.cpp, Caddy and Tailscale Serve policy."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "system"))
from files import Conflict, Files  # noqa: E402

PACKAGE_CADDY = """# The Caddyfile is an easy way to configure your Caddy web server.
#
# https://caddyserver.com/docs/caddyfile
#
# The configuration below serves a welcome page over HTTP on port 80.
# To use your own domain name (with automatic HTTPS), first make
# sure your domain's A/AAAA DNS records are properly pointed to
# this machine's public IP, then replace the line below with your
# domain name.
#
# https://caddyserver.com/docs/caddyfile/concepts#addresses
{
\t# Restrict the admin interface to a local unix file socket whose directory
\t# is restricted to caddy:caddy. By default the TCP socket allows arbitrary
\t# modification for any process and user that has access to the local
\t# interface. If admin over TCP is turned on one should make sure
\t# implications are well understood.
\tadmin "unix//run/caddy/admin.socket"
}

http:// {
\t# Set this path to your site's directory.
\troot * /usr/share/caddy

\t# Enable the static file server.
\tfile_server

\t# Another common task is to set up a reverse proxy:
\t# reverse_proxy localhost:8080

\t# Or serve a PHP site through php-fpm:
\t# php_fastcgi localhost:9000

\t# Refer to the directive documentation for more options.
\t# https://caddyserver.com/docs/caddyfile/directives
}

# Import additional caddy config files in /etc/caddy/conf.d/
import /etc/caddy/conf.d/*
"""
CADDY_MAIN = """{
\tadmin "unix//run/caddy/admin.socket"
}

import /etc/caddy/conf.d/*
"""
CADDY_SITE = """:11435 {
\tbind 127.0.0.1

\t@api path /health /v1/*
\thandle @api {
\t\treverse_proxy 127.0.0.1:11434 {
\t\t\theader_up Host 127.0.0.1:11434
\t\t}
\t}

\trespond 404
}
"""
SWITCHER_CONFIG = "/etc/llama-swap/config.yaml"
SWITCHER_UNIT = "/etc/systemd/system/llama-swap.service"
PACKAGE_CADDY_WITH_SITE = PACKAGE_CADDY.replace(
    "# Import additional caddy config files in /etc/caddy/conf.d/\n",
    CADDY_SITE + "\n# Import additional caddy config files in /etc/caddy/conf.d/\n",
)


class Native:
    def available(self, command):
        return os.access("/usr/bin/" + command, os.X_OK)

    def run(self, *args, check=True):
        try:
            result = subprocess.run(
                ["/usr/bin/" + args[0], *args[1:]],
                capture_output=True,
                text=True,
                timeout=300,
                env={"PATH": "/usr/bin", "LC_ALL": "C"},
                cwd="/",
            )
        except (OSError, subprocess.TimeoutExpired):
            raise Conflict(f"native {args[0]} unavailable or timed out") from None
        if check and result.returncode:
            raise Conflict(
                f"native {args[0]} failed; pending action retained ${result.stderr.strip() or result.stdout.strip()}"
            )
        return result


class AI:
    def __init__(self, desired, files=None, native=None):
        self.desired = desired
        self.files = files or Files()
        self.native = native or Native()
        self.updates = 0
        self.actions = 0

    def run(self, *args, **kwargs):
        return self.native.run(*args, **kwargs)

    def unit(self, name):
        output = self.run(
            "systemctl", "show", name, "--property=LoadState,ActiveState,UnitFileState"
        ).stdout
        return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)

    def require_unit(self, name):
        state = self.unit(name)
        if state.get("LoadState") != "loaded" or state.get("UnitFileState") in (
            "masked",
            "masked-runtime",
        ):
            raise Conflict("required AI system unit is missing or masked")
        return state

    def caddy_main(self):
        current = self.files.read("/etc/caddy/Caddyfile")
        if current == CADDY_MAIN:
            return current
        if not current or current in (PACKAGE_CADDY, PACKAGE_CADDY_WITH_SITE):
            return CADDY_MAIN
        if (
            'admin "unix//run/caddy/admin.socket"' in current
            and "import /etc/caddy/conf.d/*" in current
            and "http://" not in current
        ):
            return current
        raise Conflict("existing Caddyfile requires explicit adoption")

    def caddy_site(self):
        d = self.desired
        return CADDY_SITE.replace(":11435", f":{d['localPort']}").replace(
            "127.0.0.1:11434", f"127.0.0.1:{d['server']['port']}"
        )

    def switcher_config(self):
        switcher = self.desired["switcher"]
        return {
            "startPort": switcher["startPort"],
            "includeAliasesInList": switcher["includeAliasesInList"],
            "groups": switcher["groups"],
            "models": switcher["models"],
        }

    def switcher_unit(self):
        switcher = self.desired["switcher"]
        library_prefix = self.desired["source"]["installPrefix"] + "/current"
        return f"""[Unit]
Description=Nix-config llama-swap model router
After=network-online.target
Wants=network-online.target

[Service]
Environment=LD_LIBRARY_PATH={library_prefix}/lib:{library_prefix}/lib64
ExecStart={switcher["binary"]} --config {SWITCHER_CONFIG} --listen {switcher["listen"]}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

    def preset(self):
        d = self.desired
        model = d["model"]
        return f"""version = 1

[*]
parallel = {model["parallel"]}
cont-batching = true
jinja = true

[{model["id"]}]
model = {model["path"]}
device = {model["device"]}
ctx-size = {model["contextSize"]}
fit = true
fit-target = {model["fitTarget"]}
fit-ctx = {model["contextSize"]}
flash-attn = on
cache-type-k = {model["cacheTypeK"]}
cache-type-v = {model["cacheTypeV"]}
batch-size = {model["batchSize"]}
ubatch-size = {model["microBatchSize"]}
load-on-startup = true
"""

    def dropin(self):
        d = self.desired
        prefix, server = d["source"]["installPrefix"] + "/current", d["server"]
        model = d["model"]
        chat_template_kwargs = {
            key: model[option]
            for key, option in (
                ("reasoning_effort", "reasoningEffort"),
                ("enable_thinking", "enableThinking"),
                ("preserve_thinking", "preserveThinking"),
            )
            if model.get(option) is not None
        }
        chat_template_kwargs = json.dumps(
            chat_template_kwargs, separators=(",", ":")
        ).replace('"', '\\"')
        reasoning_effort = (
            f" --reasoning-effort {model['reasoningEffort']}"
            if model.get("reasoningEffort") is not None
            else ""
        )
        return f"""[Unit]
After=network-online.target

[Service]
Environment=LD_LIBRARY_PATH={prefix}/lib:{prefix}/lib64
ExecStart=
ExecStart={prefix}/bin/llama-server --models-preset /etc/llama/server/models.ini --models-max {server["modelsMax"]} --host {server["host"]} --port {server["port"]} --no-webui --temp {model["temperature"]} --top-p {model["topP"]} --top-k {model["topK"]} --min-p {model["minP"]} --presence-penalty {model["presencePenalty"]} --repeat-penalty {model["repetitionPenalty"]}{reasoning_effort} --chat-template-kwargs {chat_template_kwargs}
SupplementaryGroups=render video
Restart=on-failure
RestartSec=3
"""

    def preflight(self, installed=False):
        d, f = self.desired, self.files
        if not d["llama"]:
            return False
        if any(not Path(model["path"]).is_absolute() for model in d["models"].values()):
            raise Conflict("model paths must be absolute")
        install_prefix = d["source"]["installPrefix"]
        current = f.path(install_prefix + "/current", symlink_leaf=True)
        desired_link = (
            f"revisions/{d['source']['revision']}-"
            f"{d['source']['grammarRepetitionThreshold']}"
        )
        if not current.exists() and not current.is_symlink():
            return False
        if not current.is_symlink() or os.readlink(current) != desired_link:
            raise Conflict(
                "prepared llama-server selector does not match the declaration"
            )
        revision_prefix = install_prefix + "/" + desired_link
        executable = f.path(revision_prefix + "/bin/llama-server")
        receipt = f.read(revision_prefix + "/nix-config-build").strip()
        models = [f.path(model["path"]) for model in d["models"].values()]
        if (
            not executable.is_file()
            or any(not model.is_file() for model in models)
            or not receipt
        ):
            return False
        expected = (
            f"{d['source']['revision']} {d['source']['grammarRepetitionThreshold']}"
        )
        if receipt != expected:
            raise Conflict(
                "prepared llama-server receipt does not match the declaration"
            )
        f.read(SWITCHER_CONFIG)
        f.read(SWITCHER_UNIT)
        legacy_preset = f.read("/etc/llama/server/models.ini")
        legacy_dropin = f.read(
            "/etc/systemd/system/llama-server.service.d/60-nix-config.conf"
        )
        if legacy_preset and legacy_preset != self.preset():
            raise Conflict("legacy llama-server preset requires explicit adoption")
        if legacy_dropin and legacy_dropin != self.dropin():
            raise Conflict("legacy llama-server drop-in requires explicit adoption")
        if f.read("/etc/systemd/system/llama-server.service.d/60-local.conf"):
            raise Conflict(
                "legacy llama-server drop-in requires explicit operator adoption"
            )
        f.pending("ai-llama")
        if d["proxy"]:
            self.caddy_main()
            f.read("/etc/caddy/conf.d/nix-config-llama.caddy")
            if f.read("/etc/caddy/conf.d/nix-config-ollama.caddy"):
                raise Conflict(
                    "legacy Ollama Caddy site requires explicit operator adoption"
                )
            f.pending("ai-caddy")
            f.pending("ai-serve")
        if installed:
            required = {"systemctl", "curl"}
            if d["proxy"]:
                required |= {"caddy", "stat", "systemd-tmpfiles", "tailscale"}
            if any(not self.native.available(command) for command in required):
                raise Conflict("a required native AI command is missing")
            if d["proxy"]:
                self.require_unit("caddy.service")
        return True

    def write(self, path, text, action):
        if self.files.matches(path, text):
            return False
        self.files.mark(action)
        self.updates += int(self.files.write(path, text))
        return True

    def ensure_service(self, name, action, restart=False):
        state = self.require_unit(name)
        if state.get("UnitFileState") != "enabled":
            self.files.mark(action)
            self.run("systemctl", "enable", name)
            self.actions += 1
        if state.get("ActiveState") != "active" or restart:
            self.files.mark(action)
            self.run("systemctl", "restart" if restart else "start", name)
            self.actions += 1
        state = self.require_unit(name)
        if (
            state.get("ActiveState") != "active"
            or state.get("UnitFileState") != "enabled"
        ):
            raise Conflict("required AI service did not become ready")

    def _curl_ready(self, port, endpoint="/v1/models", retries=10, delay=2):
        url = f"http://127.0.0.1:{port}{endpoint}"
        last_err = ""
        for attempt in range(1, retries + 1):
            try:
                self.run("curl", "--fail", "--silent", "--show-error", url)
                return
            except Conflict as exc:
                last_err = str(exc)
                if attempt < retries:
                    time.sleep(delay)
        raise Conflict(f"curl failed after {retries} retries; last: {last_err}")

    def converge(self):
        d, f = self.desired, self.files
        if not d["llama"]:
            print("AI services unmanaged.")
            return
        if not self.preflight(installed=True):
            print("AI services skipped: selected model is not prepared.")
            return
        config = json.dumps(self.switcher_config(), indent=2, sort_keys=True) + "\n"
        config_changed = self.write(SWITCHER_CONFIG, config, "ai-llama")
        unit_changed = self.write(SWITCHER_UNIT, self.switcher_unit(), "ai-llama")
        pending = f.pending("ai-llama")
        if config_changed or unit_changed or pending:
            self.run("systemctl", "daemon-reload")
            self.actions += 1
        if f.read("/etc/llama/server/models.ini") or f.read(
            "/etc/systemd/system/llama-server.service.d/60-nix-config.conf"
        ):
            self.run("systemctl", "disable", "--now", "llama-server.service")
            self.actions += 1
        self.ensure_service(
            "llama-swap.service",
            "ai-llama",
            restart=pending or config_changed,
        )
        self._curl_ready(d["server"]["port"])
        f.clear("ai-llama")
        if d["proxy"]:
            self.write("/etc/caddy/Caddyfile", self.caddy_main(), "ai-caddy")
            self.write(
                "/etc/caddy/conf.d/nix-config-llama.caddy",
                self.caddy_site(),
                "ai-caddy",
            )
            pending = f.pending("ai-caddy")
            runtime_dir = self.run(
                "stat", "--format=%a:%U:%G", "/run/caddy", check=False
            )
            if (
                runtime_dir.returncode
                or runtime_dir.stdout.strip() != "750:caddy:caddy"
            ):
                self.run(
                    "systemd-tmpfiles", "--create", "/usr/lib/tmpfiles.d/caddy.conf"
                )
            self.run(
                "caddy",
                "validate",
                "--config",
                "/etc/caddy/Caddyfile",
                "--adapter",
                "caddyfile",
            )
            state = self.require_unit("caddy.service")
            repair = state.get("ActiveState") != "active"
            self.ensure_service("caddy.service", "ai-caddy", restart=repair)
            kind = self.run(
                "stat", "--format=%F", "/run/caddy/admin.socket"
            ).stdout.strip()
            if kind != "socket":
                raise Conflict("Caddy admin endpoint is not a Unix socket")
            if pending:
                self.run(
                    "caddy",
                    "reload",
                    "--config",
                    "/etc/caddy/Caddyfile",
                    "--address",
                    "unix//run/caddy/admin.socket",
                )
                self.actions += 1
            f.clear("ai-caddy")
            self._curl_ready(d["localPort"])
            status = self.run("tailscale", "serve", "status", "--json").stdout
            target = f"http://127.0.0.1:{d['localPort']}"
            port = str(d["httpsPort"])
            if target not in status or port not in status:
                if status.strip() not in ("", "{}", "null"):
                    raise Conflict(
                        "existing Tailscale Serve configuration requires explicit adoption"
                    )
                f.mark("ai-serve")
                self.run("tailscale", "serve", "--bg", f"--https={port}", target)
                self.actions += 1
                status = self.run("tailscale", "serve", "status", "--json").stdout
                if target not in status or port not in status:
                    raise Conflict("Tailscale Serve route did not converge")
            f.clear("ai-serve")
        print(
            f"AI services converged: {self.updates} files updated, {self.actions} runtime actions."
        )


def main():
    if (
        len(sys.argv) != 3
        or sys.argv[2] not in ("preflight", "converge")
        or os.geteuid() != 0
    ):
        raise Conflict("private AI adapter must be invoked by arch-switch")
    ai = AI(json.loads(Path(sys.argv[1]).read_text()))
    ai.preflight() if sys.argv[2] == "preflight" else ai.converge()


if __name__ == "__main__":
    try:
        main()
    except Conflict as error:
        print(f"AI services: {error}.", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, KeyError):
        print(
            "AI services failed; review native prerequisites and pending actions.",
            file=sys.stderr,
        )
        sys.exit(1)
