#!/usr/bin/env python3
"""Update devflow in every other folder that has it installed.

    python3 scripts/update-installs.py

A local-scope install is one entry per folder, and `claude plugin update` has
no flag that names a folder: it updates the one it runs in. deploy.sh updates
the main checkout itself, because that one must not fail. This runs the same
update in every other folder ~/.claude/plugins/installed_plugins.json names,
project folders and worktrees alike, so no project stays on an old copy.

A folder that is gone is skipped. An update that fails is one line, and the
rest still run: another project's problem does not fail a devflow deploy. So
this always exits 0.

Nor may it hold one up. An update that does not answer in 20 seconds is a
failed one, and all of them together get 60: the folders left after that are
named and not run. ship runs Verify soon after the Deploy line, so a deploy
that waits on another project is a deploy that fails. DEVFLOW_UPDATE_TIMEOUT
and DEVFLOW_UPDATE_BUDGET change the two, in seconds.
"""

import json
import os
import subprocess
import time

PLUGIN = "devflow@eddiechok-devflow"
TIMEOUT = float(os.environ.get("DEVFLOW_UPDATE_TIMEOUT", "20"))
BUDGET = float(os.environ.get("DEVFLOW_UPDATE_BUDGET", "60"))

main_checkout = os.path.realpath(os.path.dirname(subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    capture_output=True, text=True, check=True).stdout.strip()))

path = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
try:
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)["plugins"][PLUGIN]
except (OSError, ValueError, KeyError) as err:
    print(f"✗ update: cannot read the install list — {err}")
    entries = []

# A user-scope entry names no folder. The update rewrites the list as it goes,
# so the folders are read once, here.
seen = {main_checkout}
folders = []
for entry in entries:
    folder = entry.get("projectPath")
    if not folder or entry.get("scope") != "local":
        continue
    if os.path.realpath(folder) not in seen:
        seen.add(os.path.realpath(folder))
        folders.append(folder)

deadline = time.monotonic() + BUDGET
for folder in folders:
    if not os.path.isdir(folder):
        print(f"– update: {folder} is gone — skipped")
        continue
    left = deadline - time.monotonic()
    if left <= 0:
        print(f"– update: {folder} not reached — out of time")
        continue
    limit = min(TIMEOUT, left)
    try:
        proc = subprocess.run(
            ["claude", "plugin", "update", PLUGIN, "--scope", "local"],
            cwd=folder, capture_output=True, text=True, timeout=limit)
        failed = proc.returncode != 0
        said = (proc.stdout + proc.stderr).strip().splitlines()
    except subprocess.TimeoutExpired:
        failed, said = True, [f"no answer in {limit:g}s"]
    except OSError as err:
        failed, said = True, [str(err)]
    if failed:
        print(f"✗ update: {folder} — {said[-1] if said else 'no output'}")
    else:
        print(f"✓ update: {folder}")
