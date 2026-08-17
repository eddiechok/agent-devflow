#!/usr/bin/env python3
"""devflow bash-guard — PreToolUse hook for the Bash tool.

Two jobs:

  1. truncate     Rewrap long check commands so failures and the exit code
                  survive but tens of thousands of tokens of noise do not.
                  A FAILING command shows MORE output, not less — failure is
                  exactly when you want detail.

                  A rewrapped command is also allowed by this hook. It has to
                  be: permissions are checked against the rewrapped form, and
                  no Bash rule can match a compound statement. See truncate().

  2. branch-guard Ask before committing straight to the default branch.

This is an ergonomic speed bump, NOT a security control. It matches text in
command strings and is trivially bypassed by variable indirection, aliases or
a different binary. It stops accidents, not attackers.

Note the direction of that trade: for the narrow set of commands matching
CHECK_RE, this hook grants permission rather than withholding it.

Fails open by design. Any error, any uncertainty, any missing tool: the command
runs unchanged. A guard that blocks your work is worse than one that misses a
case. If python3 is unavailable the hook cannot start at all, which Claude Code
treats as a non-blocking error, so the command still runs.

Opt-outs, both documented in the README:
  # devflow-ok   appended to a command  -> skip every check
  --verbose      anywhere in a command  -> skip truncation
"""

import json
import re
import subprocess
import sys


def passthrough():
    """Allow the command through untouched."""
    print(json.dumps({}))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        passthrough()

    if payload.get("tool_name") != "Bash":
        passthrough()

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        passthrough()

    if "# devflow-ok" in command:
        passthrough()

    cwd = payload.get("cwd") or None

    if COMMIT_RE.search(command):
        guard_branch(command, cwd)

    if "--verbose" in command:
        passthrough()

    truncate(command, tool_input)


# --------------------------------------------------------------- branch guard

COMMIT_RE = re.compile(r"\bgit\s+(commit|push)\b")


def _git(args, cwd):
    try:
        out = subprocess.run(
            ["git"] + args, capture_output=True, text=True, timeout=5, cwd=cwd
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def guard_branch(command, cwd):
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    default = _git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd)
    if default:
        default = default.split("/", 1)[-1]
    else:
        # No remote HEAD configured. Fall back to the conventional names only
        # when the current branch is one of them, so we never guess wrong.
        if branch in ("main", "master"):
            default = branch

    # Only guard when we are confident. Unknown state means allow.
    if not branch or not default or branch != default:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"This writes straight to '{branch}', the default branch. "
                "devflow expects a feature branch. Continue only if you meant to. "
                "Append '# devflow-ok' to the command to skip this check."
            ),
        }
    }))
    sys.exit(0)


# ------------------------------------------------------------------ truncation

# Only rewrap commands that produce a wall of check output. Everything else is
# left completely alone.
CHECK_RE = re.compile(
    r"\b("
    r"(npm|pnpm|yarn|bun)\s+(run\s+)?(test|typecheck|lint|build|check)"
    r"|(jest|vitest|mocha|ava|playwright|cypress)"
    r"|pytest|tox|(python3?\s+-m\s+(pytest|unittest))"
    r"|go\s+(test|build|vet)"
    r"|cargo\s+(test|build|clippy|check)"
    r"|(mvn|gradle|\./gradlew)\s+\S*(test|build)"
    r"|(bundle\s+exec\s+)?rspec|rake\s+test"
    r"|dotnet\s+(test|build)"
    r"|(tsc|eslint|ruff|mypy|flake8|black|prettier)"
    r"|make\s+(test|check|lint|build)"
    r")\b",
    re.IGNORECASE,
)

# Already shaped by the caller, or contains control flow whose meaning we would
# risk changing. Leave both alone.
ALREADY_SHAPED = re.compile(r"(\|\s*(head|tail|grep)\b|>\s*/dev/null|2>&1)")
CONTROL_FLOW = ("&&", "||", ";", "|", "\n", "$(", "`")

FAIL_PAT = (
    "error|fail|failed|failing|assert|expect|panic|traceback|exception"
    "|✕|✗|×|✘|ERR!|cannot find|not found|undefined|refused"
)


def truncate(command, tool_input):
    if not CHECK_RE.search(command):
        passthrough()
    if ALREADY_SHAPED.search(command):
        passthrough()
    if any(tok in command for tok in CONTROL_FLOW):
        passthrough()

    # On success a short tail is enough — summary lines live at the end.
    # On failure: matching lines AND a longer tail, because truncation must
    # never fight the signal it exists to surface.
    wrapped = (
        'devflow_out=$(mktemp); '
        '{ ' + command + ' ; } >"$devflow_out" 2>&1; devflow_ec=$?; '
        'if [ "$devflow_ec" -eq 0 ]; then '
        'tail -n 15 "$devflow_out"; '
        'else '
        'grep -nEi "' + FAIL_PAT + '" "$devflow_out" | head -n 60; '
        'echo "--- last 40 lines ---"; '
        'tail -n 40 "$devflow_out"; '
        'fi; '
        'echo "exit=$devflow_ec"; '
        'rm -f "$devflow_out"; '
        'exit $devflow_ec'
    )

    updated = dict(tool_input)
    updated["command"] = wrapped

    # The rewrite has to carry its own permission decision.
    #
    # Claude Code checks permissions against the command this hook hands back,
    # not the one the model typed. The wrapped form is a compound statement,
    # and Bash permission rules cannot match those at all -- so without an
    # explicit allow here, `npm test` is refused however the human writes
    # their rules, and the model quietly runs the underlying runner instead,
    # going around the very command CLAUDE.md told it to use.
    #
    # What this grants is narrower than it looks. Everything above has already
    # run: the command matched CHECK_RE, a fixed list of check runners, and it
    # contains no &&, ||, ;, |, newline, $( or backtick. So only a single,
    # simple invocation of a known check runner ever reaches this line.
    #
    # It is still a grant. `npm test` runs whatever package.json says, and
    # this bypasses the human's own rules for that one class of command.
    # Append '# devflow-ok' to opt a command out of the hook entirely.
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                "devflow rewrapped this check command to trim its output. "
                "No Bash permission rule can match the rewrapped form, so the "
                "hook carries the decision itself."
            ),
            "updatedInput": updated,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a bug in this hook block real work.
        passthrough()
