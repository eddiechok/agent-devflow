#!/usr/bin/env python3
"""The Verify line: the main checkout's install is on the merged commit.

    python3 scripts/verify-deploy.py

Passes only when ~/.claude/plugins/installed_plugins.json has an entry for
devflow whose folder is the main checkout and whose commit is origin/main,
and its copy holds no file git does not track (prune-install.py --check).
The cache directory named after the commit is no proof: it exists as soon as
any folder updates, a worktree included.
"""

import json
import os
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          check=True).stdout.strip()


main_checkout = os.path.dirname(
    git("rev-parse", "--path-format=absolute", "--git-common-dir"))
merged = git("rev-parse", "origin/main")

path = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
with open(path, encoding="utf-8") as fh:
    entries = json.load(fh)["plugins"]["devflow@eddiechok-devflow"]

if not any(e.get("projectPath") == main_checkout
           and e.get("gitCommitSha") == merged for e in entries):
    print(f"✗ verify: no install entry for {main_checkout} on {merged[:7]}")
    sys.exit(1)
print(f"✓ verify: {main_checkout} is on {merged[:7]}")
# The copy must hold only tracked files: the update copies everything else too.
prune = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prune-install.py")
sys.exit(subprocess.run([sys.executable, prune, "--check"]).returncode)
