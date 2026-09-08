"""Converge Arch-owned Ollama, Caddy and Tailscale Serve policy."""

import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "system"))
from files import Conflict, Files, assignments  # noqa: E402


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

\treverse_proxy 127.0.0.1:11434 {
\t\theader_up Host 127.0.0.1:11434
\t}
}
"""


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
            raise Conflict(f"native {args[0]} failed; pending action retained")
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
        if not current or current == PACKAGE_CADDY:
            return CADDY_MAIN
        if (
            'admin "unix//run/caddy/admin.socket"' in current
            and "import /etc/caddy/conf.d/*" in current
            and "http://" not in current
        ):
            return current
        raise Conflict("existing Caddyfile requires explicit adoption")

    def preflight(self, installed=False):
        d, f = self.desired, self.files
        if not d["ollama"]:
            return
        if d["vulkan"]:
            devices = d.get("visibleDevices")
            if not devices or len(devices) != len(set(devices)):
                raise Conflict("reviewed Ollama Vulkan device IDs are required")
            existing = assignments(f.read("/etc/ollama-vulkan.conf"))
            if set(existing) - {
                "OLLAMA_VULKAN",
                "GGML_VK_VISIBLE_DEVICES",
                "OLLAMA_KEEP_ALIVE",
            }:
                raise Conflict(
                    "existing Ollama Vulkan configuration requires explicit adoption"
                )
        f.read("/etc/systemd/system/ollama.service.d/60-nix-config.conf")
        f.pending("ai-ollama")
        if d["proxy"]:
            self.caddy_main()
            f.read("/etc/caddy/conf.d/nix-config-ollama.caddy")
            f.pending("ai-caddy")
            f.pending("ai-serve")
        if installed:
            required = {"systemctl", "curl"}
            if d["proxy"]:
                required |= {"caddy", "stat", "systemd-tmpfiles", "tailscale"}
            if any(not self.native.available(command) for command in required):
                raise Conflict("a required native AI command is missing")
            self.require_unit("ollama.service")
            if d["proxy"]:
                self.require_unit("caddy.service")

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

    def converge(self):
        self.preflight(installed=True)
        d, f = self.desired, self.files
        if not d["ollama"]:
            print("AI services unmanaged.")
            return
        if d["vulkan"]:
            env = (
                "OLLAMA_VULKAN=1\n"
                + "GGML_VK_VISIBLE_DEVICES="
                + ",".join(map(str, d["visibleDevices"]))
                + "\n\n# Recommended for low-latency completion after the first model load.\n"
                + f"OLLAMA_KEEP_ALIVE={d['keepAlive']}\n"
            )
            self.write("/etc/ollama-vulkan.conf", env, "ai-ollama")
            dropin = (
                '[Service]\nEnvironment="OLLAMA_HOST=127.0.0.1:11434"\n'
                "EnvironmentFile=/etc/ollama-vulkan.conf\nSupplementaryGroups=render\n"
            )
        else:
            dropin = (
                '[Service]\nEnvironment="OLLAMA_HOST=127.0.0.1:11434"\n'
                f'Environment="OLLAMA_KEEP_ALIVE={d["keepAlive"]}"\n'
                'Environment="OLLAMA_VULKAN=0"\n'
            )
        changed = self.write(
            "/etc/systemd/system/ollama.service.d/60-nix-config.conf",
            dropin,
            "ai-ollama",
        )
        pending = f.pending("ai-ollama")
        if changed:
            self.run("systemctl", "daemon-reload")
            self.actions += 1
        self.ensure_service("ollama.service", "ai-ollama", restart=pending)
        f.clear("ai-ollama")
        if d["proxy"]:
            self.write("/etc/caddy/Caddyfile", self.caddy_main(), "ai-caddy")
            self.write(
                "/etc/caddy/conf.d/nix-config-ollama.caddy", CADDY_SITE, "ai-caddy"
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
            self.run(
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "http://127.0.0.1:11435/api/version",
            )
            status = self.run("tailscale", "serve", "status", "--json").stdout
            target = "http://127.0.0.1:11435"
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
