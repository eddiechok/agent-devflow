#!/usr/bin/env python3
"""The Lint check: `claude plugin validate .` with its one expected warning.

    python3 scripts/validate-plugin.py

The plugin has no `version` field on purpose: with none, `/plugin update`
picks up every push. So validate passes with exactly one warning, about that
field. This passes on that and nothing else: a second warning, a different
one, none at all, or a failed validate. It never adds `--strict`, which would
turn the one intended warning into an error.
"""

import subprocess
import sys

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
if len(warnings) != 1 or "version:" not in warnings[0]:
    print(f"✗ validate: expected one warning, about version; got {len(warnings)}")
    for warning in warnings:
        print(f"  {warning}")
    sys.exit(1)
print("✓ validate: the one expected warning, about version")
