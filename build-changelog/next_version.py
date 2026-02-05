import semver
import sys

version_arg = sys.argv[1].lstrip("v") if len(sys.argv) > 1 and sys.argv[1] else "0.0.0"
current_version = semver.VersionInfo.parse(version_arg)
next_release = len(sys.argv) > 2 and sys.argv[2] or "patch"

print(getattr(current_version, f"bump_{next_release}")())
