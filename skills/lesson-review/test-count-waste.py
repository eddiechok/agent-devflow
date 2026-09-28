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
                "message": {"content": [{"type": "text", "text": "– **review** clean — nothing to challenge\n\n"
                                         "## Worst of each\n- Built right: none\n"
                                         "- Security: skipped — no security item touched\n"
                                         "- Right thing: none"}]},
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

# The shape a real Deep run leaves: `flow` prints its size line, calls
# `submit` through the Skill tool, `submit` calls `review` the same way, and
# `submit`'s recap repeats the size line at the end. Found on the real
# ~/.claude/projects: `review` started by the Skill tool counted as no run,
# and the recap counted as a second `flow` run.
with tempfile.TemporaryDirectory() as root:
    proj = os.path.join(root, "-Users-eddiechok-Github-personal-fixture-repo")

    def skill_call(skill):
        return {
            "type": "assistant",
            "attributionSkill": "devflow:flow",
            "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": skill}}]},
        }

    def said(text):
        return {
            "type": "assistant",
            "attributionSkill": "devflow:flow",
            "message": {"content": [{"type": "text", "text": text}]},
        }

    write_jsonl(
        os.path.join(proj, "eeeeeeee-0000-0000-0000-000000000005.jsonl"),
        [
            {"type": "user", "message": {"content": "<command-name>/devflow:flow</command-name>"}},
            said("Deep — new skill and a new loop across skills."),
            skill_call("devflow:submit"),
            skill_call("devflow:review"),
            said("## Worst of each\n- Built right: none\n- Security: none\n- Right thing: none"),
            said("Deep — new skill and a new loop across skills.\n\n– **review** clean"),
        ],
    )

    # A second review, in its own session, that found something. The harness
    # saves the skill's own text as an isMeta user record, and review's text
    # names "nothing to challenge" -- found on the real files, where it made
    # every review read as clean. So does a test run's output.
    write_jsonl(
        os.path.join(proj, "ffffffff-0000-0000-0000-000000000006.jsonl"),
        [
            skill_call("devflow:review"),
            {"type": "user", "isMeta": True,
             "message": {"content": [{"type": "text", "text": "Base directory for this skill: x\n"
                                      "or: nothing to challenge — the first axis was clean"}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result",
                                         "content": "ok   review: nothing to review since"}]}},
            said("## Blocking\n- the scanner misses a line"),
        ],
    )

    nested = cw.scan(root, since=None)
    check("a size line repeated in the recap is one flow run, not two",
          len(nested["flow_runs"]) == 1, nested["flow_runs"])
    nested_review = nested["review_runs"].get("devflow:review")
    check("a review started by the Skill tool is counted as a run",
          nested_review is not None and nested_review["runs"] == 2, nested["review_runs"])
    check("only the clean one counts as no findings -- not the skill's own text",
          nested_review is not None and nested_review["no_findings"] == 1, nested["review_runs"])

# Three more shapes, from the review of this script. `attributionSkill` keeps
# saying `devflow:flow` between commands, so a second typed `/devflow:flow`
# looked like no change at all. Built-ins like `/model` and other plugins'
# skills are not devflow's, and must not be charged as if they were. And
# `review` prints "nothing to challenge" when only its first axis is clean --
# the spec axis can still have found something.
with tempfile.TemporaryDirectory() as root:
    proj = os.path.join(root, "-Users-eddiechok-Github-personal-fixture-repo")

    def typed(command):
        return {"type": "user", "message": {"content": f"<command-name>{command}</command-name>"}}

    def flow_said(text):
        return {"type": "assistant", "attributionSkill": "devflow:flow",
                "message": {"content": [{"type": "text", "text": text}]}}

    def review_said(text):
        return {"type": "assistant", "attributionSkill": "devflow:review",
                "message": {"content": [{"type": "text", "text": text}]}}

    write_jsonl(
        os.path.join(proj, "99999999-0000-0000-0000-000000000009.jsonl"),
        [
            typed("/devflow:flow"),
            flow_said("Quick — one."),
            typed("/devflow:flow"),
            flow_said("Standard — two."),
            typed("/model"),
            {"type": "user", "toolDenialKind": "user-rejected"},
            {"type": "user", "message": {"content": "yes to all"}, "origin": {"kind": "human"}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": "superpowers:brainstorming"}}]}},
            {"type": "user", "toolDenialKind": "permission-rule"},
            typed("/devflow:review"),
            review_said("## Worst of each\n- Built right: a loose scanner\n- Security: none\n"
                        "- Right thing: none"),
            typed("/devflow:review"),
            review_said("– **review** clean — nothing to challenge\n\n## Worst of each\n"
                        "- Built right: none\n- Security: none\n- Right thing: the export is missing"),
        ],
    )

    more = cw.scan(root, since=None)
    check("a second typed /devflow:flow is a second run",
          [r["size"] for r in more["flow_runs"]] == ["Quick", "Standard"], more["flow_runs"])
    check("a built-in command is not a devflow skill",
          not any(k.startswith("devflow:model") for k in list(more["denials"]) + list(more["yes_to_all"])),
          (more["denials"], more["yes_to_all"]))
    check("waste after a built-in command stays charged to the devflow skill",
          more["denials"].get("devflow:flow", {}).get("user-rejected") == 1
          and more["yes_to_all"].get("devflow:flow") == 1,
          (more["denials"], more["yes_to_all"]))
    check("another plugin's skill is left out of the counts",
          all(k.startswith("devflow:") for k in more["denials"]), more["denials"])
    more_review = more["review_runs"].get("devflow:review")
    check("two typed reviews are two runs",
          more_review is not None and more_review["runs"] == 2, more["review_runs"])
    check("a review whose spec axis found something is not clean",
          more_review is not None and more_review["no_findings"] == 0, more["review_runs"])

# Round 2 of the review, both found on the real files. Real reports bold
# the Worst of each labels. And a human's follow-up request in a session
# where `flow` is already loaded gets a new size line with no new start --
# while `submit`'s recap, after `submit` starts, must still not count.
with tempfile.TemporaryDirectory() as root:
    proj = os.path.join(root, "-Users-eddiechok-Github-personal-fixture-repo")

    def human(text):
        return {"type": "user", "message": {"content": text}, "origin": {"kind": "human"}}

    def plain(text):
        return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}

    def skill(name):
        return {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}

    write_jsonl(
        os.path.join(proj, "88888888-0000-0000-0000-000000000008.jsonl"),
        [
            skill("devflow:flow"),
            plain("Standard — first request."),
            skill("devflow:submit"),
            skill("devflow:review"),
            plain("## Worst of each\n- **Built right:** none.\n- **Security:** skipped — no security"
                  " item touched\n- **Right thing:** no spec, axis skipped."),
            plain("Standard — first request.\n\n✓ **review** 0 found"),
            human("now also tighten the copy"),
            plain("Quick — follow-up on #12, same branch."),
            skill("devflow:submit"),
            plain("Quick — follow-up on #12, same branch."),
            # The final look's case: a typed `/devflow:submit` is itself a
            # human record, and so is a plain reply before the recap.
            human("<command-name>/devflow:flow</command-name>"),
            plain("Deep — third request."),
            human("<command-name>/devflow:submit</command-name>"),
            human("yes to all"),
            plain("Deep — third request.\n\n✓ **pr** opened #15"),
        ],
    )

    last = cw.scan(root, since=None)
    check("a clean review with bold labels counts as no findings",
          last["review_runs"].get("devflow:review", {}).get("no_findings") == 1, last["review_runs"])
    check("a follow-up request's size line is its own run; recaps are not",
          [r["size"] for r in last["flow_runs"]] == ["Standard", "Quick", "Deep"], last["flow_runs"])

# From the review of the whole branch. A resumed or forked session copies the
# same records, uuids and all, into a second file -- and one session id can be
# saved under two project folders. Each record counts once. And a reply that
# says "yes to all" among other words still says it.
with tempfile.TemporaryDirectory() as root:
    records = [
        {"uuid": "u1", "type": "user", "message": {"content": "<command-name>/devflow:flow</command-name>"}},
        {"uuid": "u2", "type": "assistant", "attributionSkill": "devflow:flow",
         "message": {"content": [{"type": "text", "text": "Deep — one job."}]}},
        {"uuid": "u3", "type": "user", "message": {"content": "Yes to all, go ahead."},
         "origin": {"kind": "human"}},
    ]
    write_jsonl(os.path.join(root, "-proj-a", "11111111-0000-0000-0000-000000000001.jsonl"), records)
    write_jsonl(os.path.join(root, "-proj-a--claude-worktrees-x",
                             "11111111-0000-0000-0000-000000000001.jsonl"), records)
    write_jsonl(os.path.join(root, "-proj-a", "22222222-0000-0000-0000-000000000002.jsonl"),
                records + [{"uuid": "u4", "type": "assistant", "attributionSkill": "devflow:flow",
                            "message": {"content": [{"type": "text", "text": "Quick — a second job."}]}}])

    dup = cw.scan(root, since=None)
    check("a record copied into another file counts once",
          [r["size"] for r in dup["flow_runs"]] == ["Deep", "Quick"], dup["flow_runs"])
    check("a copied yes-to-all counts once, and a longer reply still counts",
          dup["yes_to_all"].get("devflow:flow") == 1, dup["yes_to_all"])

# Round 2 of that review. Session ids are random, so a fork's file can sort
# before the original's: the older file must still own the run and its cost.
# A file of nothing but copies still has its own subagents. And "not yes to
# all" is not a yes.
with tempfile.TemporaryDirectory() as root:
    proj = os.path.join(root, "-proj-b")
    original = [
        {"uuid": "o1", "type": "user", "timestamp": "2026-09-01T00:00:00.000Z",
         "message": {"content": "<command-name>/devflow:flow</command-name>"}},
        {"uuid": "o2", "type": "assistant", "attributionSkill": "devflow:flow",
         "timestamp": "2026-09-01T00:00:01.000Z",
         "message": {"content": [{"type": "text", "text": "Deep — the original."}]}},
        {"uuid": "o3", "type": "user", "timestamp": "2026-09-01T00:00:02.000Z",
         "message": {"content": "Not yes to all, ask me about each one."}, "origin": {"kind": "human"}},
        {"type": "cost-state", "totalCostUSD": 1.0, "totalDuration": 1000},
    ]
    write_jsonl(os.path.join(proj, "bbbbbbbb-0000-0000-0000-00000000000b.jsonl"), original)
    write_jsonl(os.path.join(proj, "bbbbbbbb-0000-0000-0000-00000000000b", "subagents", "agent-9.jsonl"),
                [{"uuid": "s1", "type": "user", "toolDenialKind": "user-rejected"}])
    with open(os.path.join(proj, "bbbbbbbb-0000-0000-0000-00000000000b", "subagents", "agent-9.meta.json"),
              "w", encoding="utf-8") as f:
        json.dump({"agentType": "devflow:reviewer"}, f)
    write_jsonl(os.path.join(proj, "aaaaaaaa-0000-0000-0000-00000000000a.jsonl"),
                original[:3] + [{"type": "cost-state", "totalCostUSD": 9.0, "totalDuration": 9000}])
    # Written a moment apart, the two files can share one timestamp. Set them
    # an hour and a minute apart. On a Mac, an mtime set before the birth time
    # moves the birth time back with it.
    import time
    hour_ago = time.time() - 3600
    os.utime(os.path.join(proj, "bbbbbbbb-0000-0000-0000-00000000000b.jsonl"), (hour_ago, hour_ago))
    os.utime(os.path.join(proj, "aaaaaaaa-0000-0000-0000-00000000000a.jsonl"),
             (hour_ago + 60, hour_ago + 60))

    order = cw.scan(root, since=None)
    check("the older file owns a copied run, and its own cost",
          [(r["session"][:8], r["cost_usd"]) for r in order["flow_runs"]] == [("bbbbbbbb", 1.0)],
          order["flow_runs"])
    check("a session's subagents are counted even when its main file is all copies",
          order["denials"].get("devflow:reviewer", {}).get("user-rejected") == 1, order["denials"])
    check("'not yes to all' is not a yes to all",
          order["yes_to_all"] == {}, order["yes_to_all"])

# Issue #63. A session quit partway through `review`, before its Worst of each
# block, then resumed into a new file: the resumed file finishes the run.
with tempfile.TemporaryDirectory() as root:
    proj = os.path.join(root, "-proj-c")
    started = [
        {"uuid": "r1", "type": "user", "timestamp": "2026-09-02T00:00:00.000Z",
         "message": {"content": "<command-name>/devflow:review</command-name>"}},
        {"uuid": "r2", "type": "assistant", "attributionSkill": "devflow:review",
         "timestamp": "2026-09-02T00:00:01.000Z",
         "message": {"content": [{"type": "text", "text": "Reading the diff."}]}},
    ]
    write_jsonl(os.path.join(proj, "cccccccc-0000-0000-0000-00000000000c.jsonl"), started)
    write_jsonl(os.path.join(proj, "dddddddd-0000-0000-0000-00000000000d.jsonl"), started + [
        {"uuid": "r3", "type": "assistant", "attributionSkill": "devflow:review",
         "timestamp": "2026-09-02T01:00:00.000Z",
         "message": {"content": [{"type": "text", "text":
                     "## Worst of each\n- Built right: none\n- Security: skipped\n- Right thing: none"}]}},
    ])
    # Only the review is still open at the end of this third file, and no
    # later file finishes it: it counts where it started, as one that found
    # something.
    write_jsonl(os.path.join(proj, "eeeeeeee-0000-0000-0000-00000000000e.jsonl"), [
        {"uuid": "q1", "type": "user", "timestamp": "2026-09-03T00:00:00.000Z",
         "message": {"content": "<command-name>/devflow:review</command-name>"}},
    ])

    resumed = cw.scan(root, since=None)
    check("a review resumed mid-run is finished by the file it resumed into",
          resumed["review_runs"].get("devflow:review") == {"runs": 2, "no_findings": 1},
          resumed["review_runs"])

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
