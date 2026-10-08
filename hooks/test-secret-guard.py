#!/usr/bin/env python3
"""Contract tests for secret-guard.py.

    python3 hooks/test-secret-guard.py

Like bash-guard, the hook is a pure stdin->stdout script, so its whole
contract can be checked for free: which file names ask, which pass, and that
it fails open. Every check also asserts the hook exits 0 and prints valid
JSON, because a crash means the edit goes ahead with no question asked.
"""

import json
import os
import subprocess
import sys

# Overridable so you can point the suite at a deliberately broken copy and
# watch it go red. A test that has never been seen to fail is not evidence.
HOOK = os.environ.get(
    "SECRET_GUARD",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret-guard.py"),
)

passed = 0
failed = 0


def run(stdin):
    proc = subprocess.run(
        [sys.executable, HOOK], input=stdin,
        capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return json.loads(proc.stdout or "{}")


def call(file_path=None, tool="Edit", tool_input=None):
    """Run the hook on one payload and return its parsed decision."""
    payload = {"tool_name": tool, "cwd": "/repo"}
    payload["tool_input"] = (
        tool_input if tool_input is not None else {"file_path": file_path}
    )
    return run(json.dumps(payload))


def decision(out):
    return (out.get("hookSpecificOutput") or {}).get("permissionDecision")


def reason(out):
    return (out.get("hookSpecificOutput") or {}).get("permissionDecisionReason") or ""


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        print(f"ok   {name}")
        passed += 1
    else:
        print(f"FAIL {name}")
        if detail:
            print(f"     {detail}")
        failed += 1


# ------------------------------------------------------- secret env files ask

for tool, path in [
    ("Edit", "/repo/.env"),
    ("Write", "/repo/.env"),
    ("MultiEdit", "/repo/.env"),
    ("Edit", "/repo/apps/api/.env.local"),
    ("Write", "/repo/.env.production"),
    ("Edit", "/repo/.env.development.local"),
]:
    out = call(path, tool=tool)
    check(f"asks before {tool} on {path}",
          decision(out) == "ask", f"got {out!r}")

out = call("/repo/apps/api/.env.local")
check("the ask names the file", "/repo/apps/api/.env.local" in reason(out),
      reason(out))
check("the ask says to edit it by hand", "by hand" in reason(out), reason(out))
check("the ask is a PreToolUse answer",
      (out.get("hookSpecificOutput") or {}).get("hookEventName") == "PreToolUse")

# ------------------------------------------------- templates and lookalikes pass

for name, path in [
    ("the example template", "/repo/.env.example"),
    ("the template", "/repo/.env.template"),
    ("the sample", "/repo/.env.sample"),
    ("the committed test env", "/repo/apps/api/.env.test"),
    # A Python virtualenv is often a folder called .env. Its files are code.
    ("a file inside a folder named .env", "/repo/.env/lib/site.py"),
    ("a folder named .env.local", "/repo/.env.local/notes.md"),
    ("direnv's file", "/repo/.envrc"),
    ("a name that ends in .env", "/repo/config/app.env"),
    ("a source file about env", "/repo/src/env.ts"),
]:
    out = call(path)
    check(f"passes: {name}", out == {}, f"got {out!r}")

# ------------------------------------------------------------- fails open

check("ignores Bash, which has no file_path",
      call(tool="Bash", tool_input={"command": "cat .env"}) == {})
check("ignores tools it is not about",
      call("/repo/.env", tool="Read") == {})
check("survives a payload with no file_path", call(tool_input={}) == {})
check("survives a file_path that is not a string",
      call(tool_input={"file_path": 7}) == {})
check("survives a tool_input that is not an object",
      call(tool_input=["/repo/.env"]) == {})
check("survives stdin that is not JSON", run("not json") == {})

# --------------------------------------------------------------------- report

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
