"""Arch system settings. Only packaging invokes this privileged private adapter.

The caller holds the arch-switch deployment lock. Tests inject a filesystem and
native runner directly; production accepts no root/command overrides.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from files import Conflict, Files, locale_gen, replace_keys
from firewall import Firewall


class Native:
    @staticmethod
    def available(command):
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


class System:
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

    def ready_unit(self, name):
        state = self.unit(name)
        if state.get("LoadState") != "loaded" or state.get("UnitFileState") in (
            "masked",
            "masked-runtime",
        ):
            raise Conflict("required system unit is missing or masked")
        return state

    def service(self, name, action, restart=False):
        state = self.ready_unit(name)
        if state.get("UnitFileState") != "enabled":
            self.files.mark(action)
            self.run("systemctl", "enable", name)
            self.actions += 1
        if state.get("ActiveState") != "active" or restart:
            self.files.mark(action)
            self.run("systemctl", "restart" if restart else "start", name)
            self.actions += 1
        state = self.ready_unit(name)
        if (
            state.get("ActiveState") != "active"
            or state.get("UnitFileState") != "enabled"
        ):
            raise Conflict("required system unit did not become ready")

    def write(self, path, text, action):
        if not self.files.matches(path, text):
            self.files.mark(action)
            self.updates += int(self.files.write(path, text))
            return True
        return False

    def localtime(self):
        path = self.files.path("/etc/localtime", symlink_leaf=True)
        if path.exists() and not path.is_symlink():
            raise Conflict("localtime is not a zoneinfo symlink")
        if path.is_symlink():
            target = os.readlink(path)
            # Permit the two native absolute/relative zoneinfo link forms only.
            if not (
                target.startswith("/usr/share/zoneinfo/")
                or target.startswith("../usr/share/zoneinfo/")
            ) or ".." in target.removeprefix("../").split("/"):
                raise Conflict("localtime has an unexpected symlink target")
        values = self.run("timedatectl", "show", "--property=Timezone,LocalRTC").stdout
        state = dict(line.split("=", 1) for line in values.splitlines() if "=" in line)
        if state.get("LocalRTC") != "no":
            raise Conflict("local RTC requires an explicit operator decision")
        return state.get("Timezone")

    def console(self):
        desired = self.desired["console"]
        values = {"KEYMAP": desired["keymap"]}
        if desired["font"] is not None:
            values["FONT"] = desired["font"]
        return replace_keys(self.files.read("/etc/vconsole.conf"), values)

    def check_console_assets(self):
        desired = self.desired["console"]
        for directory, key, suffixes in [
            ("keymaps", "keymap", (".map", ".map.gz")),
            ("consolefonts", "font", (".psf", ".psf.gz", ".psfu", ".psfu.gz")),
        ]:
            value = desired[key]
            if value is None:
                continue
            base = self.files.path("/usr/share/kbd/" + directory)
            found = [p for suffix in suffixes for p in base.rglob(value + suffix)]
            if not found or not all(p.is_file() and not p.is_symlink() for p in found):
                raise Conflict("console keymap or font is unavailable")

    def check_time_provider(self):
        for unit in (
            "chronyd.service",
            "chrony.service",
            "ntpd.service",
            "openntpd.service",
        ):
            state = self.unit(unit)
            if state.get("ActiveState") in (
                "active",
                "activating",
                "reloading",
            ) or state.get("UnitFileState") in (
                "enabled",
                "enabled-runtime",
                "linked",
                "linked-runtime",
            ):
                raise Conflict(
                    "another time synchronization provider is enabled or active"
                )
        # Custom servers supplement native defaults; per-link sources are not overridden.

    def check_trim(self):
        data = json.loads(
            self.run(
                "lsblk",
                "--json",
                "--bytes",
                "--output",
                "NAME,TYPE,DISC-MAX,MOUNTPOINTS",
            ).stdout
        )

        def walk(devices, encrypted=False):
            suitable = False
            for device in devices:
                crypt = encrypted or device["type"] == "crypt"
                mounted = any(device.get("mountpoints") or [])
                if mounted and crypt:
                    raise Conflict(
                        "encrypted mounted storage needs a separate discard policy"
                    )
                suitable |= mounted and int(device.get("disc-max") or 0) > 0
                suitable |= walk(device.get("children", []), crypt)
            return suitable

        if not walk(data["blockdevices"]):
            raise Conflict("no mounted discard-capable device was found")
        # A second custom fstrim timer/cron owner must be resolved by the operator.
        output = self.run(
            "systemctl", "list-timers", "--all", "--no-legend", "--no-pager"
        ).stdout
        if any(
            "fstrim" in line and "fstrim.timer" not in line
            for line in output.splitlines()
        ):
            raise Conflict("another TRIM schedule exists")
        for directory in (
            "/etc/cron.d",
            "/etc/cron.daily",
            "/etc/cron.weekly",
            "/etc/cron.monthly",
        ):
            path = self.files.path(directory)
            if path.exists() and any("trim" in p.name.lower() for p in path.iterdir()):
                raise Conflict("a possible additional TRIM schedule exists")

    def preflight(self, installed=False):
        d, f = self.desired, self.files
        if installed:
            commands = set()
            for capability, required in {
                "locale": ("locale", "locale-gen"),
                "timeZone": ("timedatectl",),
                "hostname": ("hostnamectl",),
                "timeSync": ("systemctl", "timedatectl"),
                "journal": ("systemctl", "systemd-tmpfiles", "journalctl"),
                "trim": ("systemctl", "lsblk"),
                "firewall": ("systemctl", "ufw", "iptables", "ip6tables"),
            }.items():
                if d.get(capability) is not None:
                    commands.update(required)
            if any(not self.native.available(command) for command in commands):
                raise Conflict("a required native system command is missing")
        # Read/validate all owned state before writes; no mutation during preflight.
        for capability, action in {
            "locale": "locale",
            "timeZone": "timezone",
            "hostname": "hostname",
            "timeSync": "timesyncd",
            "journal": "journald",
            "console": "console",
            "power": "power",
            "trim": "trim",
            "firewall": "firewall",
        }.items():
            if d.get(capability) is not None:
                f.pending(action)
        if d.get("locale") is not None:
            locale_gen(f.read("/etc/locale.gen"), d["locale"]["generated"])
            replace_keys(f.read("/etc/locale.conf"), {"LANG": d["locale"]["lang"]})
        if d.get("timeZone") is not None:
            if installed and not f.zone_exists(d["timeZone"]):
                raise Conflict("declared zoneinfo is unavailable")
            self.localtime()
        if d.get("hostname") is not None:
            f.read("/etc/hostname")
        for name, text in d.get("files", {}).items():
            f.dropin(name, text)
        if d.get("timeSync") is not None:
            self.check_time_provider()
            if installed:
                self.ready_unit("systemd-timesyncd.service")
        if d.get("journal") is not None and installed:
            self.ready_unit("systemd-journald.service")
        if d.get("console") is not None:
            self.console()
            if installed:
                self.check_console_assets()
        if d.get("power") is not None:
            if not f.read("/proc/sys/kernel/random/boot_id").strip():
                raise Conflict("boot identity is unavailable")
        if d.get("trim") is not None:
            f.timer_dropin()
            self.check_trim()
            if installed:
                self.ready_unit("fstrim.timer")
        if d.get("firewall") is not None:
            Firewall(self).preflight(installed)

    def converge(self):
        self.preflight(installed=True)
        d, f = self.desired, self.files
        if d.get("locale") is not None:
            value = d["locale"]
            self.write(
                "/etc/locale.gen",
                locale_gen(f.read("/etc/locale.gen"), value["generated"]),
                "locale",
            )

            def available():
                return {
                    line.lower().replace("-", "")
                    for line in self.run("locale", "-a").stdout.splitlines()
                }

            wanted = {name.lower().replace("-", "") for name in value["generated"]}
            if f.pending("locale") or not wanted <= available():
                f.mark("locale")
                self.run("locale-gen")
                self.actions += 1
                if not wanted <= available():
                    raise Conflict("required locales were not generated")
            self.write(
                "/etc/locale.conf",
                replace_keys(f.read("/etc/locale.conf"), {"LANG": value["lang"]}),
                "locale",
            )
            f.clear("locale")
        if d.get("timeZone") is not None:
            target = f.path("/etc/localtime", symlink_leaf=True)
            expected = "/usr/share/zoneinfo/" + d["timeZone"]
            matches = target.is_symlink() and os.readlink(target) in (
                expected,
                ".." + expected,
            )
            if (
                not matches
                or self.localtime() != d["timeZone"]
                or f.pending("timezone")
                or not f.metadata_matches("/etc/localtime", symlink=True)
            ):
                f.mark("timezone")
                self.run("timedatectl", "set-timezone", d["timeZone"])
                self.actions += 1
                if (
                    self.localtime() != d["timeZone"]
                    or not target.is_symlink()
                    or os.readlink(target) not in (expected, ".." + expected)
                ):
                    raise Conflict("timezone did not converge")
                self.updates += int(f.repair_metadata("/etc/localtime", symlink=True))
                f.clear("timezone")
        if d.get("hostname") is not None:
            for kind in ("--static", "--transient"):
                actual = self.run("hostnamectl", kind).stdout.strip()
                if actual != d["hostname"] or (
                    kind == "--static"
                    and f.read("/etc/hostname").strip() != d["hostname"]
                ):
                    f.mark("hostname")
                    self.run("hostnamectl", kind, "set-hostname", d["hostname"])
                    self.actions += 1
                    if self.run("hostnamectl", kind).stdout.strip() != d["hostname"]:
                        raise Conflict("hostname did not converge")
            if not f.metadata_matches("/etc/hostname"):
                f.mark("hostname")
                self.updates += int(f.repair_metadata("/etc/hostname"))
            f.clear("hostname")
        for name, text in d.get("files", {}).items():
            target = f.dropin(name, text)
            if name == "logind":
                self.power(target, text)
                continue
            self.write(target, text, name)
            pending = f.pending(name)
            if name == "timesyncd":
                self.service("systemd-timesyncd.service", name, restart=pending)
                synchronized = (
                    self.run(
                        "timedatectl", "show", "--property=NTPSynchronized", "--value"
                    ).stdout.strip()
                    == "yes"
                )
                print(
                    "Time synchronization: synchronized."
                    if synchronized
                    else "Time synchronization: waiting for network synchronization."
                )
            elif name == "journald":
                self.ready_unit("systemd-journald.service")
                if (
                    pending
                    or self.unit("systemd-journald.service").get("ActiveState")
                    != "active"
                ):
                    f.mark(name)
                    if d["journal"]["storage"] == "persistent":
                        self.run(
                            "systemd-tmpfiles", "--create", "--prefix=/var/log/journal"
                        )
                    self.run("systemctl", "restart", "systemd-journald.service")
                    if d["journal"]["storage"] in ("auto", "persistent"):
                        self.run("journalctl", "--flush")
                    self.actions += 1
                    if (
                        self.unit("systemd-journald.service").get("ActiveState")
                        != "active"
                    ):
                        raise Conflict("journald did not become ready")
            f.clear(name)
        if d.get("console") is not None:
            if self.write("/etc/vconsole.conf", self.console(), "console") or f.pending(
                "console"
            ):
                print("Console configuration is prepared for the next boot.")
            f.clear("console")
        if d.get("trim") is not None:
            path, text = f.timer_dropin()
            self.write(path, text, "trim")
            pending = f.pending("trim")
            if pending:
                # Disable catch-up, so starting an overdue timer cannot request
                # an immediate full trim during deployment. Keep native schedule.
                self.run("systemctl", "daemon-reload")
            self.service("fstrim.timer", "trim", restart=pending)
            f.clear("trim")
        if d.get("firewall") is not None:
            Firewall(self).converge()
        print(
            f"System settings converged: {self.updates} files updated, {self.actions} runtime actions."
        )
        if d.get("locale") is not None:
            print("System language applies to new login sessions.")

    def power(self, path, text):
        f = self.files
        boot = f.read("/proc/sys/kernel/random/boot_id").strip()
        digest = hashlib.sha256(text.encode()).hexdigest()
        receipt = f"{boot} {digest}\n"
        if not f.matches(path, text):
            f.mark("power", receipt)
            self.updates += int(f.write(path, text))
        if f.pending("power"):
            previous = f.read(f.marker("power")).split()
            if len(previous) != 2:
                raise Conflict("invalid power pending receipt")
            if previous[0] != boot and previous[1] == digest:
                f.clear("power")
            else:
                # Never restart logind with live sessions. A new desired value
                # after a failed write also needs a complete boot boundary.
                if previous[1] != digest:
                    f.mark("power", receipt)
                print(
                    "Power event configuration pending: reboot required; desktop inhibitors still apply."
                )


def main():
    if (
        len(sys.argv) != 3
        or sys.argv[2] not in ("preflight", "converge")
        or os.geteuid() != 0
    ):
        raise Conflict("private adapter must be invoked by arch-switch")
    system = System(json.loads(Path(sys.argv[1]).read_text()))
    if sys.argv[2] == "preflight":
        system.preflight()
    else:
        system.converge()


if __name__ == "__main__":
    try:
        main()
    except Conflict as error:
        print(f"System settings: {error}.", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, KeyError):
        # Fixed diagnostics only: exceptions may contain private native output.
        print(
            "System settings failed; review ownership, native prerequisites and pending actions using the operator guide.",
            file=sys.stderr,
        )
        sys.exit(1)
