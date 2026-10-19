#!/usr/bin/env python3
"""Contract tests for validate-plugin.py.

    python3 scripts/test-validate-plugin.py

The plugin has no `version` field on purpose: with none, `/plugin update`
picks up every push. So `claude plugin validate .` passes with exactly one
warning, about that field, and anything else is wrong. Each check runs the
script against a fake `claude` on PATH that prints a fixed answer, so the
whole contract costs nothing and needs no login.
"""

import os
import stat
import subprocess
import sys
import tempfile

# Overridable so you can point the suite at a deliberately broken copy and
# watch it go red. A test that has never been seen to fail is not evidence.
SCRIPT = os.environ.get(
    "VALIDATE_PLUGIN",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "validate-plugin.py"),
)

passed = 0
failed = 0

# What `claude plugin validate .` printed on this repo, 2026-10-19.
VERSION_WARNING = (
    '  ❯ plugins[0] plugin.json → version: No version specified. Consider '
    'adding a version following semver (e.g., "1.0.0")\n'
)
HEAD = ("Validating marketplace manifest: /repo/.claude-plugin/marketplace.json"
        "\n\n")
ONE_VERSION_WARNING = (HEAD + "⚠ Found 1 warning:\n\n" + VERSION_WARNING
                       + "\n✔ Validation passed with warnings\n")
TWO_WARNINGS = (HEAD + "⚠ Found 2 warnings:\n\n" + VERSION_WARNING
                + "  ❯ plugins[0] plugin.json → description: Description is "
                  "very short\n"
                + "\n✔ Validation passed with warnings\n")
OTHER_WARNING = (HEAD + "⚠ Found 1 warning:\n\n"
                 + "  ❯ plugins[0] plugin.json → description: Description is "
                   "very short\n"
                 + "\n✔ Validation passed with warnings\n")
NO_WARNING = HEAD + "✔ Validation passed\n"
AN_ERROR = (HEAD + "✘ Found 1 error:\n\n"
            + "  ❯ plugins[0] → source: Path does not exist\n"
            + "\n✘ Validation failed\n")


def run(output, code=0, with_claude=True):
    """Run the script with a fake claude that prints `output`, exits `code`.

    Returns (exit code, what the script printed, the args claude was given).
    """
    with tempfile.TemporaryDirectory() as d:
        out_file = os.path.join(d, "out")
        args_file = os.path.join(d, "args")
        with open(out_file, "w", encoding="utf-8") as fh:
            fh.write(output)
        if with_claude:
            fake = os.path.join(d, "claude")
            with open(fake, "w") as fh:
                fh.write(f'#!/bin/sh\nprintf "%s" "$*" > "{args_file}"\n'
                         f'/bin/cat "{out_file}"\nexit {code}\n')
            os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        env = dict(os.environ, PATH=d)
        proc = subprocess.run([sys.executable, SCRIPT], env=env,
                              capture_output=True, text=True, timeout=20)
        args = open(args_file).read() if os.path.exists(args_file) else None
        return proc.returncode, proc.stdout + proc.stderr, args


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


code, out, args = run(ONE_VERSION_WARNING)
check("passes on exactly one warning, about version", code == 0,
      f"exit {code}: {out}")
check("runs claude plugin validate . with no --strict", args == "plugin validate .",
      f"claude was given: {args!r}")
check("prints validate's own output, so the warning reaches the screen",
      "No version specified" in out, out)

code, out, _ = run(TWO_WARNINGS)
check("fails on a second warning", code != 0, f"exit {code}: {out}")
check("the failure names the extra warning", "description" in out, out)

code, out, _ = run(OTHER_WARNING)
check("fails on one warning that is not about version", code != 0,
      f"exit {code}: {out}")

code, out, _ = run(NO_WARNING)
check("fails when the version warning is gone -- the field was added", code != 0,
      f"exit {code}: {out}")

code, out, _ = run(AN_ERROR, code=1)
check("fails when validate itself fails", code != 0, f"exit {code}: {out}")

code, out, _ = run(ONE_VERSION_WARNING, code=1)
check("fails on a non-zero exit even with the right warning", code != 0,
      f"exit {code}: {out}")

code, out, _ = run("", with_claude=False)
check("fails with a message, not a traceback, when claude is missing",
      code != 0 and "Traceback" not in out and "claude" in out,
      f"exit {code}: {out}")

# --------------------------------------------------------------------- report

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
