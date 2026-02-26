import json
import os
import re
import semver
import sys


def read_fallback_version():
    if os.path.exists("package.json"):
        with open("package.json") as f:
            return json.load(f).get("version", "0.0.0")
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml") as f:
            match = re.search(r'^version\s*=\s*"(.+)"', f.read(), re.MULTILINE)
            return match.group(1) if match else "0.0.0"
    if os.path.exists("VERSION"):
        with open("VERSION") as f:
            return f.read().strip()
    return "0.0.0"


version_arg = sys.argv[1].lstrip("v") if len(sys.argv) > 1 and sys.argv[1] else "0.0.0"
try:
    current_version = semver.VersionInfo.parse(version_arg)
except ValueError:
    current_version = semver.VersionInfo.parse(read_fallback_version())
next_release = len(sys.argv) > 2 and sys.argv[2] or "patch"

print(getattr(current_version, f"bump_{next_release}")())
