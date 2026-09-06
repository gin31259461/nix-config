"""Syntax-only checks for tracked assets; never load a desktop session."""

import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1])
qmlformat = sys.argv[2]
for path in sorted((source / ".config").rglob("*.json")):
    try:
        json.loads(path.read_text())
    except ValueError:
        raise SystemExit(f"Invalid tracked JSON: {path.relative_to(source)}") from None
for path in sorted((source / ".config/quickshell/overview").rglob("*.qml")):
    result = subprocess.run(
        [qmlformat, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if result.returncode:
        raise SystemExit(f"Invalid overview QML syntax: {path.relative_to(source)}")
for path in sorted((source / ".agents/skills").rglob("*.sh")):
    subprocess.run(["bash", "-n", str(path)], check=True)
# Existing imported shell/search libraries are not automatically reformatted.
for path in sorted((source / ".config/quickshell").rglob("*.js")):
    # QML's .pragma library is a loader directive, not ECMAScript syntax.
    script = path.read_text().removeprefix(".pragma library\n")
    subprocess.run(
        ["node", "--check"],
        input=script,
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
    )
print("Tracked JSON, overview QML, skill shell syntax and JavaScript syntax passed.")
