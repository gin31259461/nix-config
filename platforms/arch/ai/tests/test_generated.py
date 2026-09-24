"""Check the Nix-built AI manifest consumed by the privileged adapter."""

import json
from pathlib import Path
import sys
import unittest

MANIFEST = Path(sys.argv.pop(1))
PACKAGE_CADDY = Path(sys.argv.pop(1))


class GeneratedArtifactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.desired = json.loads(MANIFEST.read_text())
        cls.generated = cls.desired["generated"]

    def test_router_and_unit_follow_the_declared_model_and_loopback_port(self):
        desired = self.desired
        generated = self.generated
        config = json.loads(generated["switcherConfig"])
        self.assertEqual(config["models"], desired["switcher"]["models"])
        self.assertEqual(config["startPort"], desired["server"]["port"] + 1000)
        self.assertIn(desired["switcher"]["binary"], generated["switcherUnit"])
        self.assertIn(
            f"--listen 127.0.0.1:{desired['server']['port']}",
            generated["switcherUnit"],
        )
        self.assertIn(f"--port {desired['server']['port']}", generated["legacyDropin"])
        self.assertIn(desired["model"]["path"], generated["legacyPreset"])

    def test_caddy_policy_is_loopback_only_and_keeps_package_adoption(self):
        desired = self.desired
        generated = self.generated
        site = generated["caddySite"]
        self.assertTrue(site.startswith(f":{desired['localPort']} {{\n"))
        self.assertIn("bind 127.0.0.1", site)
        self.assertIn(f"reverse_proxy 127.0.0.1:{desired['server']['port']}", site)
        self.assertIn("@api path /health /v1/*", site)
        self.assertIn("respond 404", site)
        self.assertEqual(generated["packageCaddy"], PACKAGE_CADDY.read_text())
        self.assertIn(
            generated["packageCaddy"].split("# Import additional")[0],
            generated["packageCaddyWithSite"],
        )
        self.assertIn('admin "unix//run/caddy/admin.socket"', generated["caddyMain"])


if __name__ == "__main__":
    unittest.main()
