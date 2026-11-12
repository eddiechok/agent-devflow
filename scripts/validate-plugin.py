#!/usr/bin/env python3
"""The Lint check: `claude plugin validate .` with only its known warnings.

    python3 scripts/validate-plugin.py

The plugin has no `version` field on purpose: with none, `/plugin update`
picks up every push. So validate warns about that field. This passes when it
does, and when every other warning is on the KNOWN list below. It fails on any
other warning, on no version warning at all, or on a failed validate. It never
adds `--strict`, which would turn the intended warnings into errors.
"""

import subprocess
import sys

VERSION = "version: No version specified"

# Warnings that are true and harmless here. claude 2.1.322 added the last three.
KNOWN = (
    VERSION,
    # This CLAUDE.md is for working on the repo, not context for the plugin.
    "CLAUDE.md at the plugin root is not loaded",
    # The listing icon is the plugin directory's, which this plugin is not in.
    "No icon (ICON_MISSING)",
    # A note under "About these checks", not a defect.
    "This folder also holds a marketplace manifest",
)

try:
    proc = subprocess.run(["claude", "plugin", "validate", "."],
                          capture_output=True, text=True)
except FileNotFoundError:
    print("✗ validate: no claude CLI on PATH")
    sys.exit(1)

output = proc.stdout + proc.stderr
print(output, end="")

warnings = [line.strip() for line in output.splitlines()
            if line.strip().startswith("❯")]

if proc.returncode != 0:
    print(f"✗ validate: claude plugin validate exited {proc.returncode}")
    sys.exit(1)
unknown = [w for w in warnings if not any(k in w for k in KNOWN)]
if unknown or not any(VERSION in w for w in warnings):
    print(f"✗ validate: expected the version warning and known ones only; "
          f"got {len(unknown)} unknown")
    for warning in unknown or warnings:
        print(f"  {warning}")
    sys.exit(1)
print(f"✓ validate: {len(warnings)} warning(s), all known, version among them")
