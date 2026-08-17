#!/usr/bin/env python3
"""Contract tests for bash-guard.py.

    python3 hooks/test-bash-guard.py

The hook is a pure stdin->stdout script, so its whole contract can be checked
deterministically, for free, in under a second. That matters more than it looks
for one specific rule: **the rewrite must carry its own `allow`**. That is the
regression that hurt (see README, "Allows the commands it trims"), and it is
the one thing an eval transcript cannot check reliably.

Why not: the wrapper only fires on a BARE check command. In practice Claude
writes `npm test 2>&1 | tail -25` first, which trips ALREADY_SHAPED and makes
the hook stand down -- correctly. An eval grader looking for the wrapper's
`exit=N` output therefore fails while the hook is perfectly healthy. It did,
three runs out of three. So the rule is checked here instead, where the input
is fixed and the answer cannot drift. See evals/README.md.

Every check also asserts the hook exits 0 and prints valid JSON, because it
fails open: a crash means the command runs unchanged, silently.
"""

import json
import os
import subprocess
import sys
import tempfile

# Overridable so you can point the suite at a deliberately broken copy and
# watch it go red. A test that has never been seen to fail is not evidence.
HOOK = os.environ.get(
    "BASH_GUARD",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bash-guard.py"),
)

passed = 0
failed = 0


def call(command=None, tool="Bash", cwd=None, tool_input=None):
    """Run the hook on one payload and return its parsed decision."""
    payload = {"tool_name": tool, "cwd": cwd or os.getcwd()}
    payload["tool_input"] = (
        tool_input if tool_input is not None else {"command": command}
    )
    proc = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload),
        capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return json.loads(proc.stdout or "{}")


def decision(out):
    return (out.get("hookSpecificOutput") or {}).get("permissionDecision")


def rewritten(out):
    return ((out.get("hookSpecificOutput") or {})
            .get("updatedInput") or {}).get("command", "")


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


def scratch_repo(branch):
    """A throwaway repo with one commit, on `branch`, with origin/HEAD unset.

    Unset origin/HEAD is the normal state of a fresh clone and the state that
    broke default-branch detection, so it is what the guard should be tested
    against.
    """
    d = tempfile.mkdtemp(prefix="bash-guard-test-")
    run = lambda *a: subprocess.run(a, cwd=d, capture_output=True, check=True)
    run("git", "init", "-q", "-b", "main")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "test")
    run("git", "commit", "-q", "--allow-empty", "-m", "init")
    if branch != "main":
        run("git", "checkout", "-q", "-b", branch)
    return d


# ------------------------------------------------- the rewrite, and its allow

out = call("npm test")
check("bare check command is rewrapped",
      "devflow_out=" in rewritten(out), rewritten(out)[:120])
check("the rewrite carries its own allow  <-- the regression that hurt",
      decision(out) == "allow", f"decision={decision(out)!r}")
check("the rewrite still runs the command it was given",
      "{ npm test ; }" in rewritten(out), rewritten(out)[:120])
check("the rewrite reports the exit code",
      'echo "exit=$devflow_ec"' in rewritten(out))
check("the rewrite preserves the exit status for the caller",
      rewritten(out).rstrip().endswith("exit $devflow_ec"))
check("a passing run is trimmed to a short tail",
      'tail -n 15' in rewritten(out))
check("a failing run shows MORE: matches plus a longer tail",
      'head -n 60' in rewritten(out) and 'tail -n 40' in rewritten(out))

for cmd in ("pytest", "cargo test", "go test ./...", "tsc", "npm run lint"):
    check(f"recognised as a check runner: {cmd!r}",
          decision(call(cmd)) == "allow")

# ------------------------------------------------------------ hands-off cases

for name, cmd in [
    ("already piped to tail", "npm test 2>&1 | tail -5"),
    ("already redirected", "npm test >/dev/null"),
    ("compound with &&", "npm test && npm run lint"),
    ("compound with ;", "npm test; echo done"),
    ("command substitution", "echo $(npm test)"),
    ("--verbose opts out of trimming", "npm test --verbose"),
    ("# devflow-ok opts out entirely", "npm test  # devflow-ok"),
    ("not a check runner", "ls -la"),
    ("empty command", "   "),
]:
    check(f"passes through untouched: {name}", call(cmd) == {},
          f"got {call(cmd)!r}")

check("ignores non-Bash tools",
      call(tool="Write", tool_input={"file_path": "/tmp/x"}) == {})
check("survives a payload with no command field",
      call(tool="Bash", tool_input={}) == {})

# -------------------------------------------------------------- branch guard

repo = scratch_repo("main")
out = call("git commit -m 'x'", cwd=repo)
check("asks before committing to the default branch",
      decision(out) == "ask", f"decision={decision(out)!r}")
check("the ask explains itself and names the opt-out",
      "devflow-ok" in ((out.get("hookSpecificOutput") or {})
                       .get("permissionDecisionReason") or ""))
check("guards push as well as commit",
      decision(call("git push origin main", cwd=repo)) == "ask")
check("# devflow-ok skips the branch guard too",
      call("git commit -m 'x'  # devflow-ok", cwd=repo) == {})

feature = scratch_repo("feat/thing")
check("stays quiet on a feature branch",
      call("git commit -m 'x'", cwd=feature) == {},
      f"got {call('git commit -m x', cwd=feature)!r}")

check("stays quiet where there is no repo at all",
      call("git commit -m 'x'", cwd=tempfile.mkdtemp()) == {})

# --------------------------------------------------------------------- report

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
