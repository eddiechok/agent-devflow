#!/usr/bin/env python3
"""Keep only the files git tracks in the main checkout's devflow install.

    python3 scripts/prune-install.py           # delete the rest
    python3 scripts/prune-install.py --check   # list the rest, exit 1 if any

The update copies the whole main checkout into the plugin cache, gitignored
files too: other sessions' worktrees under .claude/worktrees, the local
settings, __pycache__. Claude Code has no ignore file for that copy, so the
deploy prunes it after the update. Only an install inside
~/.claude/plugins/cache is touched: one that loads in place is the checkout
itself, and what git does not track there is somebody's work. What Claude Code
writes there itself, .in_use/<pid> for a loaded install and .orphaned_at for
an unused one, stays: it reads them when it cleans the cache up.
"""

import json
import os
import subprocess
import sys


CLAUDE_OWN = {".in_use", ".orphaned_at", "node_modules"}


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout


check_only = sys.argv[1:] == ["--check"]
main_checkout = os.path.realpath(os.path.dirname(
    git("rev-parse", "--path-format=absolute", "--git-common-dir").strip()))
tracked = set(git("ls-files", "-z", cwd=main_checkout).split("\0")) - {""}

plugins = os.path.expanduser("~/.claude/plugins")
with open(os.path.join(plugins, "installed_plugins.json"), encoding="utf-8") as fh:
    entries = json.load(fh)["plugins"]["devflow@eddiechok-devflow"]
# A user-scope entry names no folder, and realpath("") is the one we stand in.
installs = [e["installPath"] for e in entries
            if e.get("installPath") and e.get("projectPath")
            and os.path.realpath(e["projectPath"]) == main_checkout]
if not installs:
    print(f"✗ prune: no install entry for {main_checkout}")
    sys.exit(1)
install = os.path.realpath(installs[0])
if not install.startswith(os.path.realpath(os.path.join(plugins, "cache")) + os.sep):
    print(f"– prune: {install} is not in the plugin cache — left alone")
    sys.exit(0)

extra = []
for root, dirs, files in os.walk(install):
    links = [d for d in dirs if os.path.islink(os.path.join(root, d))]
    dirs[:] = [d for d in dirs if d not in links]
    if root == install:
        dirs[:] = [d for d in dirs if d not in CLAUDE_OWN]
        files = [f for f in files if f not in CLAUDE_OWN]
    for name in files + links:
        path = os.path.join(root, name)
        if os.path.relpath(path, install).replace(os.sep, "/") not in tracked:
            extra.append(path)

if check_only:
    if extra:
        shown = ", ".join(os.path.relpath(p, install) for p in extra[:3])
        print(f"✗ prune: {install} holds {len(extra)} files git does not track"
              f" — {shown}")
        sys.exit(1)
    print(f"✓ prune: {install} holds only tracked files")
    sys.exit(0)

for path in extra:
    os.remove(path)
# Deepest first, so a folder emptied by the one below it goes too.
for root, dirs, files in sorted(os.walk(install), reverse=True):
    top = os.path.relpath(root, install).split(os.sep)[0]
    if root != install and top not in CLAUDE_OWN and not os.listdir(root):
        os.rmdir(root)
print(f"✓ prune: removed {len(extra)} files git does not track from {install}")
