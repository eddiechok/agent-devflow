#!/usr/bin/env python3
"""devflow secret-guard — PreToolUse hook for the Edit, Write and MultiEdit tools.

Asks before Claude edits a secret env file: `.env`, or any `.env.*` except
the four that are meant to be committed -- `.env.example`, `.env.template`,
`.env.sample` and `.env.test`. Only the file's own name counts, so a file
inside a folder called `.env` (a Python virtualenv, often) is left alone.

It asks rather than blocks. The human answers the prompt, so there is no
opt-out to write down: saying yes is the opt-out.

This is an ergonomic speed bump, NOT a security control. It sees only the
Edit, Write and MultiEdit tools. `echo KEY=1 >> .env` through Bash goes
straight past it, and so does any other way of writing a file.

Fails open by design, like bash-guard. Any error, any payload it does not
understand: the edit goes ahead unchanged.
"""

import json
import os
import sys

TOOLS = ("Edit", "Write", "MultiEdit")
TEMPLATES = (".env.example", ".env.template", ".env.sample", ".env.test")


def passthrough():
    """Allow the edit through untouched."""
    print(json.dumps({}))
    sys.exit(0)


def is_secret(path):
    name = os.path.basename(path)
    if name in TEMPLATES:
        return False
    return name == ".env" or name.startswith(".env.")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        passthrough()

    if not isinstance(payload, dict) or payload.get("tool_name") not in TOOLS:
        passthrough()

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        passthrough()

    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_secret(path):
        passthrough()

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"{path} looks like a secret env file. devflow asks before "
                "Claude edits one. Say no and edit it by hand if it holds "
                "real keys."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let a bug in this hook block real work.
        passthrough()
