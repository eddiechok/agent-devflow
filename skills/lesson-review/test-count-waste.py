#!/usr/bin/env python3
"""Contract tests for count-waste.py.

    python3 skills/lesson-review/test-count-waste.py

Claude Code's saved-session format has no docs, so this suite does not test
against the real `~/.claude/projects` -- it builds small fixture `.jsonl`
files in a temp dir, shaped like the real records looked when a real
directory was read to find them (see docs/lessons.md and the commit that
added this file). No network, no real `~/.claude`.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "count-waste.py")

# The file is named with a hyphen, like every other skill script in this
# repo, so it cannot be a plain `import` -- load it by path instead.
_spec = importlib.util.spec_from_file_location("count_waste", SCRIPT)
cw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cw)

passed = 0
failed = 0


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


def write_jsonl(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            if isinstance(line, str):
                f.write(line + "\n")
            else:
                f.write(json.dumps(line) + "\n")


def build_fixture(root):
    proj = os.path.join(root, "-Users-eddiechok-Github-personal-fixture-repo")

    # Session A: a `flow` run, sized Standard, one "yes to all", one denied
    # permission prompt, one line the parser cannot make sense of, and the
    # session's final cost-state record.
    session_a = "aaaaaaaa-0000-0000-0000-000000000001"
    write_jsonl(
        os.path.join(proj, session_a + ".jsonl"),
        [
            {
                "type": "user",
                "message": {"content": "<command-message>devflow:flow</command-message>\n<command-name>/devflow:flow</command-name>"},
                "timestamp": "2026-09-20T00:00:00.000Z",
            },
            {
                "type": "assistant",
                "attributionSkill": "devflow:flow",
                "message": {
                    "content": [
                        {"type": "text", "text": "Standard — follow-up on #12, tightening the copy it added."}
                    ]
                },
                "timestamp": "2026-09-20T00:00:01.000Z",
            },
            {
                "type": "user",
                "message": {"content": "yes to all"},
                "origin": {"kind": "human"},
                "timestamp": "2026-09-20T00:00:02.000Z",
            },
            {
                "type": "user",
                "message": {"content": [{"type": "tool_result", "content": "denied", "is_error": True}]},
                "toolDenialKind": "user-rejected",
                "timestamp": "2026-09-20T00:00:03.000Z",
            },
            "not json at all",
            {
                "type": "cost-state",
                "sessionId": session_a,
                "totalCostUSD": 1.23,
                "totalDuration": 5000,
            },
        ],
    )

    # Session B: a `review` run that found nothing.
    session_b = "bbbbbbbb-0000-0000-0000-000000000002"
    write_jsonl(
        os.path.join(proj, session_b + ".jsonl"),
        [
            {
                "type": "user",
                "message": {"content": "<command-name>/devflow:review</command-name>"},
                "timestamp": "2026-09-21T00:00:00.000Z",
            },
            {
                "type": "assistant",
                "attributionSkill": "devflow:review",
                "message": {"content": [{"type": "text", "text": "– **review** clean — nothing to challenge"}]},
                "timestamp": "2026-09-21T00:00:01.000Z",
            },
        ],
    )

    # Session C: a `review` run that found something -- not counted as
    # "no findings".
    session_c = "cccccccc-0000-0000-0000-000000000003"
    write_jsonl(
        os.path.join(proj, session_c + ".jsonl"),
        [
            {
                "type": "user",
                "message": {"content": "<command-name>/devflow:review</command-name>"},
                "timestamp": "2026-09-22T00:00:00.000Z",
            },
            {
                "type": "assistant",
                "attributionSkill": "devflow:review",
                "message": {"content": [{"type": "text", "text": "## Blocking\n- the thing is broken"}]},
                "timestamp": "2026-09-22T00:00:01.000Z",
            },
        ],
    )

    # Session D: old, before --since -- must be excluded when asked.
    session_d = "dddddddd-0000-0000-0000-000000000004"
    write_jsonl(
        os.path.join(proj, session_d + ".jsonl"),
        [
            {
                "type": "user",
                "message": {"content": "<command-name>/devflow:flow</command-name>"},
                "timestamp": "2026-01-01T00:00:00.000Z",
            },
            {
                "type": "user",
                "message": {"content": "yes to all"},
                "origin": {"kind": "human"},
                "timestamp": "2026-01-01T00:00:01.000Z",
            },
        ],
    )

    # Session A also has a subagent file saved beside it, the way a real
    # devflow:review run saves `reviewer`'s transcript beside the main one.
    write_jsonl(
        os.path.join(proj, session_a, "subagents", "agent-1.jsonl"),
        [
            {
                "type": "user",
                "isSidechain": True,
                "message": {"content": "review this"},
                "timestamp": "2026-09-20T00:00:04.000Z",
            },
            {
                "type": "user",
                "toolDenialKind": "user-rejected",
                "timestamp": "2026-09-20T00:00:05.000Z",
            },
        ],
    )
    with open(
        os.path.join(proj, session_a, "subagents", "agent-1.meta.json"), "w", encoding="utf-8"
    ) as f:
        json.dump({"agentType": "devflow:reviewer"}, f)

    return proj


def run_cli(args):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


with tempfile.TemporaryDirectory() as root:
    proj = build_fixture(root)

    report = cw.scan(root, since=None)

    check(
        "yes-to-all charged to the skill that asked",
        report["yes_to_all"].get("devflow:flow") == 2,
        report["yes_to_all"],
    )

    check(
        "denials counted by kind, charged to the skill running at the time",
        report["denials"].get("devflow:flow", {}).get("user-rejected") == 1,
        report["denials"],
    )

    check(
        "a subagent's denial is charged to its own agent type",
        report["denials"].get("devflow:reviewer", {}).get("user-rejected") == 1,
        report["denials"],
    )

    check("approvals are reported as not recorded", report["approvals"] == "not recorded")

    flow_runs = report["flow_runs"]
    check("one flow run found", len(flow_runs) == 1, flow_runs)
    if flow_runs:
        run = flow_runs[0]
        check("the flow run's size is Standard", run["size"] == "Standard", run)
        check(
            "the flow run carries the session's cost-state totals",
            run["duration_ms"] == 5000 and run["cost_usd"] == 1.23,
            run,
        )

    review = report["review_runs"].get("devflow:review")
    check("two review runs counted", review is not None and review["runs"] == 2, review)
    check(
        "one of the two review runs reported no findings",
        review is not None and review["no_findings"] == 1,
        review,
    )

    check(
        "the one unparsable line is skipped and counted, not crashed on",
        report["skipped_lines"] >= 1,
        report["skipped_lines"],
    )

    check("four sessions scanned", report["sessions_scanned"] == 4, report["sessions_scanned"])

    since_report = cw.scan(root, since="2026-09-01")
    check(
        "--since drops the old session's yes-to-all",
        since_report["yes_to_all"].get("devflow:flow") == 1,
        since_report["yes_to_all"],
    )
    check(
        "--since still scans the sessions on or after the date",
        since_report["sessions_scanned"] == 3,
        since_report["sessions_scanned"],
    )

    # The CLI itself: plain table, then --json, on the same fixture tree.
    plain = run_cli(["--projects-dir", root])
    check("the plain CLI exits 0", plain.returncode == 0, plain.stderr)
    check("the plain table names the flow skill", "devflow:flow" in plain.stdout, plain.stdout)

    as_json = run_cli(["--projects-dir", root, "--json"])
    check("the --json CLI exits 0", as_json.returncode == 0, as_json.stderr)
    try:
        parsed = json.loads(as_json.stdout)
        json_ok = parsed["sessions_scanned"] == 4
    except (json.JSONDecodeError, KeyError):
        json_ok = False
    check("--json prints a machine-readable report", json_ok, as_json.stdout[:200])

    # A file the parser cannot open at all (e.g. a directory pretending to
    # be a session) must not crash the scan.
    os.makedirs(os.path.join(proj, "not-really-a-session.jsonl"))
    no_crash = run_cli(["--projects-dir", root])
    check(
        "a session file that cannot be read is skipped, not fatal",
        no_crash.returncode == 0,
        no_crash.stderr,
    )

# A directory with nothing in it produces a clean, empty report rather than
# an error -- the script has to run on a real ~/.claude/projects, and empty
# projects dirs are the common case there too.
with tempfile.TemporaryDirectory() as empty_root:
    empty_report = cw.scan(empty_root, since=None)
    check("an empty projects dir scans clean", empty_report["sessions_scanned"] == 0)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
