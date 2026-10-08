#!/usr/bin/env python3
"""Contract tests for evals/run.py.

Nothing here calls Claude. These test the two parts of the runner that can be
wrong silently: the YAML subset parser, and the graders. Both fail in the
direction this repo cares about — a grader that scores a run nobody made, and a
parser that reads a case file as something other than what it says.

Run: python3 evals/test-run.py
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

passed = 0
failed = 0


def check(name, got, want):
    global passed, failed
    if got == want:
        print("ok   " + name)
        passed += 1
    else:
        print("FAIL " + name)
        print("       got:  " + repr(got))
        print("       want: " + repr(want))
        failed += 1


def check_true(name, got):
    check(name, bool(got), True)


# ------------------------------------------------------------------ the parser

check(
    "parser: plain scalar",
    run.parse_yaml("name: sizing-quick\n"),
    {"name": "sizing-quick"},
)

check(
    "parser: quoted scalar keeps a # that is not a comment",
    run.parse_yaml('pattern: "# pass \\\\d"\n'),
    {"pattern": "# pass \\d"},
)

check(
    "parser: a bare # after a space is a comment",
    run.parse_yaml("runs: 3  # three of them\n"),
    {"runs": 3},
)

check(
    "parser: a whole-line comment is dropped",
    run.parse_yaml("# leading note\nname: x\n"),
    {"name": "x"},
)

check(
    "parser: ints stay ints, and quoted digits stay strings",
    run.parse_yaml('a: 3\nb: "1.1"\n'),
    {"a": 3, "b": "1.1"},
)

check(
    "parser: booleans",
    run.parse_yaml("exists: true\ngone: false\n"),
    {"exists": True, "gone": False},
)

check(
    "parser: flow sequence",
    run.parse_yaml("tags: [sizing, flow, danger-list]\n"),
    {"tags": ["sizing", "flow", "danger-list"]},
)

check(
    "parser: nested map",
    run.parse_yaml("context:\n  scaffold_script: ./scaffold.sh\n"),
    {"context": {"scaffold_script": "./scaffold.sh"}},
)

check(
    "parser: list of maps",
    run.parse_yaml(
        "graders:\n"
        "  - type: tool_used\n"
        "    name: routes-to-build\n"
        "    min: 1\n"
        "  - type: regex\n"
        "    name: announces\n"
    ),
    {
        "graders": [
            {"type": "tool_used", "name": "routes-to-build", "min": 1},
            {"type": "regex", "name": "announces"},
        ]
    },
)

check(
    "parser: a map nested inside a list item",
    run.parse_yaml(
        "graders:\n"
        "  - type: tool_order\n"
        "    before:\n"
        "      tool: Skill\n"
        "      input_match: devflow:build\n"
        "    after:\n"
        "      tool: Skill\n"
        "      input_match: devflow:submit\n"
    ),
    {
        "graders": [
            {
                "type": "tool_order",
                "before": {"tool": "Skill", "input_match": "devflow:build"},
                "after": {"tool": "Skill", "input_match": "devflow:submit"},
            }
        ]
    },
)

check(
    "parser: folded block scalar joins its lines",
    run.parse_yaml("criteria: >\n  first line\n  second line\nname: after\n"),
    {"criteria": "first line second line", "name": "after"},
)

# The parser must refuse what it does not understand rather than guess. A case
# file that quietly reads as half of itself is the failure this whole runner
# exists to avoid.
try:
    run.parse_yaml("anchors: &a\n  x: 1\nuse: *a\n")
    check("parser: refuses an anchor rather than guessing", "no error", "an error")
except run.CaseError:
    check("parser: refuses an anchor rather than guessing", "an error", "an error")

try:
    run.parse_yaml("key: |\n  literal block\n")
    check("parser: refuses a literal block rather than guessing", "no error", "an error")
except run.CaseError:
    check("parser: refuses a literal block rather than guessing", "an error", "an error")

# Every real case file in this repo has to survive the parser. This is the test
# that actually keeps it honest: the subset is defined by what the repo uses.
for name in sorted(os.listdir(HERE)):
    case_path = os.path.join(HERE, name, "case.yaml")
    if not os.path.isfile(case_path):
        continue
    with open(case_path) as fh:
        doc = run.parse_yaml(fh.read())
    check_true("parser: %s has a name" % name, doc.get("name") == name)
    check_true("parser: %s has an execution prompt" % name,
               isinstance(doc.get("execution", {}).get("prompt"), str))
    check_true("parser: %s has graders" % name,
               isinstance(doc.get("graders"), list) and len(doc["graders"]) > 0)
    check_true("parser: %s every grader has a type and a name" % name,
               all(g.get("type") and g.get("name") for g in doc["graders"]))

check_true("parser: found the case files to check", passed > 10)

# A session that never started is an error, not a scored run. The CLI
# answers "Not logged in" as a one-turn success with cost 0, and scoring
# that as FAIL reads as the plugin failing.
try:
    run.events_or_raise([
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Not logged in \u00b7 Please run /login"}]}},
        {"type": "result", "subtype": "success", "num_turns": 1, "total_cost_usd": 0},
    ])
    check("runner: a not-logged-in session raises, not scores", "no error", "CaseError")
except run.CaseError as exc:
    check("runner: a not-logged-in session raises, not scores", "CaseError", "CaseError")
    check_true("runner: the error says to log in", "log" in str(exc).lower())

# A manual case stays out of the default set and comes in when named.
names = [c["name"] for c in run.load_cases(None)]
check_true("cases: a manual case is left out by default", "plans-on-tracker" not in names)
names = [c["name"] for c in run.load_cases("plans-on-*")]
check_true("cases: a manual case runs when named", names == ["plans-on-tracker"])

# Spot-check one value the naive parser would get wrong.
with open(os.path.join(HERE, "full-loop", "case.yaml")) as fh:
    full_loop = run.parse_yaml(fh.read())
merge_graders = [g for g in full_loop["graders"] if "merge" in str(g.get("input_match", ""))]
check(
    "parser: full-loop's merge graders survive with their trailing space",
    sorted(g["input_match"] for g in merge_graders),
    ["gh pr merge", "git merge "],
)

# #94: Standard and Deep now wait for go after the todo block, and in -p mode
# nobody answers. So a case that must reach a skill flow only calls after that
# stop says so in its prompt, the way deep-coordinator already did for Deep.
# Found from the graders, not a list: the first version named two cases and
# missed bug-routes-to-debug.
PAST_THE_GO = ("devflow:build", "devflow:debug", "devflow:builder",
               "devflow:plan", "devflow:submit")
_past_go_cases = []
for _c in run.load_cases(None):
    _needs = [g for g in _c["graders"]
              if g.get("type") == "tool_used" and g.get("min", 0) >= 1
              and g.get("input_match") in PAST_THE_GO]
    if _needs:
        _past_go_cases.append(_c["name"])
        check_true(f"{_c['name']}: the prompt tells the run not to wait for go",
                   "do not wait" in _c["execution"]["prompt"])
        # #110: on Deep "yes to all" answers the questions and no longer
        # approves the plan, so the prompt has to say go as well.
        check_true(f"{_c['name']}: the prompt says go",
                   re.search(r"\bgo\b", _c["execution"]["prompt"]) is not None)
check_true("cases: the go scan found the cases that build past the stop",
           {"full-loop", "bug-routes-to-build", "bug-routes-to-debug",
            "deep-coordinator"} <= set(_past_go_cases))

# plans-on-tracker is a manual case, so the scan above never loads it. It
# reaches devflow:plan past Deep's go too (#110).
with open(os.path.join(HERE, "plans-on-tracker", "case.yaml")) as fh:
    _tracker = run.parse_yaml(fh.read())
check_true("plans-on-tracker: the prompt says go",
           re.search(r"\bgo\b", _tracker["execution"]["prompt"]) is not None)

# `deep-coordinator` is the case that measures the Deep loop, and the loop is
# now chains in parallel, merged back, then submit. The merge is the new
# promise and the easiest one to skip silently, so the case carries a grader
# for it -- and every grader that was already there stays.
with open(os.path.join(HERE, "deep-coordinator", "case.yaml")) as fh:
    deep = run.parse_yaml(fh.read())
deep_graders = {g["name"]: g for g in deep["graders"]}

check_true(
    "deep-coordinator: every earlier grader is still there",
    {"announces-deep", "does-not-build-in-session", "reaches-submit",
     "builders-run-before-submit", "relays-the-builder-report",
     "agents-were-not-refused", "never-reaches-ship"} <= set(deep_graders),
)

# #112: the case could never reach two chains. Its two pieces both edited
# src/greet.js and src/cli.js, and plan never lets two chains share a file, so
# it made one chain. And the fixture had no worktree.baseRef, so plan wrote it
# and, on that same run, built sequentially with no merge. Now the pieces live
# in different files, and the scaffold sets the base before the session starts.
_deep_prompt = deep["execution"]["prompt"]
check_true("deep-coordinator: the two pieces live in different files  <-- #112",
           "src/farewell.js" in _deep_prompt and "lang option" not in _deep_prompt
           and "no CLI change" in _deep_prompt)

# The real scaffold.sh runs beside a stub greeter.sh that only makes a repo:
# the real one runs npm and node, and this test needs python3 and git alone.
_tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_tmp, "case"))
    os.makedirs(os.path.join(_tmp, "fixtures"))
    shutil.copy(os.path.join(HERE, "deep-coordinator", "scaffold.sh"),
                os.path.join(_tmp, "case", "scaffold.sh"))
    with open(os.path.join(_tmp, "fixtures", "greeter.sh"), "w") as fh:
        fh.write('#!/usr/bin/env bash\nset -e\nmkdir -p "$1"\ngit init -q "$1"\n')
    os.chmod(os.path.join(_tmp, "fixtures", "greeter.sh"), 0o755)
    _ws = os.path.join(_tmp, "ws")
    _scaffold = subprocess.run(
        ["bash", os.path.join(_tmp, "case", "scaffold.sh"), _ws],
        capture_output=True, text=True)
    _local = os.path.join(_ws, ".claude", "settings.local.json")
    _base = None
    if os.path.isfile(_local):
        with open(_local) as fh:
            _base = json.load(fh).get("worktree", {}).get("baseRef")
    check("deep-coordinator: the scaffold sets worktree.baseRef = head  <-- #112",
          [_scaffold.returncode, _base], [0, "head"])
    check("deep-coordinator: the setting leaves the tree clean  <-- #112",
          subprocess.run(["git", "-c", "core.excludesFile=/dev/null",
                          "status", "--porcelain"], cwd=_ws,
                         capture_output=True, text=True).stdout, "")
finally:
    shutil.rmtree(_tmp, ignore_errors=True)

_merges = deep_graders.get("merges-the-chains", {})
check(
    "deep-coordinator: the merge grader watches Bash for a --no-ff merge",
    [_merges.get("type"), _merges.get("tool"), _merges.get("input_match"),
     _merges.get("min"), _merges.get("weight")],
    ["tool_used", "Bash", "git merge --no-ff", 1, 2],
)

check_true(
    "deep-coordinator: the case says chains, in both halves of its prose",
    "chain" in deep["description"] and "chain" in deep["expected_outcome"],
)

# ------------------------------------------------------------------- the trace

SKILL_BODY = "Announce it:\n\nQuick — single-file copy change.\n\nDeep — new subsystem."

EVENTS = [
    {"type": "system", "subtype": "init", "slash_commands": ["devflow:flow"]},
    {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": "devflow:flow"}},
    ]}},
    # The rendered SKILL.md comes back as a tool result. It is input to the
    # model, not something the model said.
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": SKILL_BODY},
    ]}},
    {"type": "assistant", "message": {"content": [
        {"type": "text", "text": "Standard — changing existing behaviour."},
        {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "npm test"}},
    ]}},
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t2", "content": "# pass 4\nexit=0"},
    ]}},
    {"type": "result", "result": "done"},
]

trace = run.build_trace(EVENTS)

check_true("trace: includes what the assistant said", "Standard — changing" in trace)
check_true("trace: includes a tool the assistant ran", "npm test" in trace)
check_true("trace: includes ordinary tool output", "# pass 4" in trace)
check_true(
    "trace: EXCLUDES a rendered skill body  <-- the false pass this prevents",
    "single-file copy change" not in trace,
)
check_true("trace: excludes the whole skill body, not just one line",
           "new subsystem" not in trace)

# A skill that points at `references/<name>.md` has the model `Read` it, and a
# reference file carries worked examples of the very lines graders look for --
# `split-and-park.md` holds `✓ **chips** 2 offered`. A `Read` of a skill's own
# file is the skill body arriving by another tool, so it is dropped the same way.
READ_EVENTS = [
    {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "r1", "name": "Read", "input": {
            "file_path": "/p/devflow/skills/flow/references/split-and-park.md"}},
        {"type": "tool_use", "id": "r2", "name": "Read", "input": {
            "file_path": "/tmp/project/greet.py"}},
    ]}},
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "r1", "content": "✓ **chips** 2 offered"},
        {"type": "tool_result", "tool_use_id": "r2", "content": "def greet(name):"},
    ]}},
]
read_trace = run.build_trace(READ_EVENTS)
check_true("trace: EXCLUDES a Read of a skill's reference file",
           "**chips** 2 offered" not in read_trace)
check_true("trace: still includes a Read of a project file",
           "def greet(name):" in read_trace)

check(
    "trace: tool calls are found in order",
    [c["name"] for c in run.tool_calls(EVENTS)],
    ["Skill", "Bash"],
)

# --------------------------------------------------------------- the graders


def ctx(events=EVENTS, workdir="."):
    return run.Context(events=events, trace=run.build_trace(events), workdir=workdir)


def verdict(grader, c=None):
    return run.grade_one(grader, c or ctx())[0]


check("grader: tool_used min met",
      verdict({"type": "tool_used", "tool": "Skill", "input_match": "devflow:flow", "min": 1}),
      "pass")

check("grader: tool_used min not met",
      verdict({"type": "tool_used", "tool": "Skill", "input_match": "devflow:submit", "min": 1}),
      "fail")

check("grader: tool_used max 0 with no match",
      verdict({"type": "tool_used", "tool": "Skill", "input_match": "devflow:ship", "max": 0}),
      "pass")

check("grader: tool_used max 0 with a match",
      verdict({"type": "tool_used", "tool": "Bash", "input_match": "npm test", "max": 0}),
      "fail")

# A subagent's tool calls ARE in the parent's stream-json trace, tagged with
# `parent_tool_use_id`. deep-coordinator's first paid run found this the hard
# way: its "the session never calls build itself" grader fired on the two
# builders' own calls to build. `session_only` counts the session's calls and
# not its agents'; the default still counts both, so no older case changes.
SUBAGENT_BUILD = EVENTS[:-1] + [
    {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
        {"type": "tool_use", "id": "t3", "name": "Agent",
         "input": {"subagent_type": "devflow:builder", "prompt": "piece 1"}},
    ]}},
    {"type": "assistant", "parent_tool_use_id": "t3", "message": {"content": [
        {"type": "tool_use", "id": "t4", "name": "Skill", "input": {"skill": "devflow:build"}},
    ]}},
    {"type": "result", "result": "done"},
]

check("grader: tool_used counts a subagent's call by default",
      verdict({"type": "tool_used", "tool": "Skill", "input_match": "devflow:build", "min": 1},
              ctx(SUBAGENT_BUILD)),
      "pass")

check("grader: tool_used session_only ignores a subagent's call  <-- deep-coordinator run 1",
      verdict({"type": "tool_used", "tool": "Skill", "input_match": "devflow:build",
               "max": 0, "session_only": True}, ctx(SUBAGENT_BUILD)),
      "pass")

check("grader: tool_used session_only still sees the session's own call",
      verdict({"type": "tool_used", "tool": "Agent", "input_match": "devflow:builder",
               "min": 1, "session_only": True}, ctx(SUBAGENT_BUILD)),
      "pass")

# The bug this runner was written to check. `git merge` prefixes `git merge-base`,
# which submit step 5 tells the assistant to run.
MERGE_BASE = [{"type": "assistant", "message": {"content": [
    {"type": "tool_use", "id": "m", "name": "Bash",
     "input": {"command": "git merge-base HEAD origin/main"}},
]}}]

check("grader: 'git merge ' does not fire on git merge-base  <-- the grader fix",
      verdict({"type": "tool_used", "tool": "Bash", "input_match": "git merge ", "max": 0},
              ctx(MERGE_BASE)),
      "pass")

check("grader: the old bare pattern would have fired on it",
      verdict({"type": "tool_used", "tool": "Bash", "input_match": "git merge", "max": 0},
              ctx(MERGE_BASE)),
      "fail")

REAL_MERGE = [{"type": "assistant", "message": {"content": [
    {"type": "tool_use", "id": "m", "name": "Bash",
     "input": {"command": "git merge --ff-only origin/main"}},
]}}]

check("grader: 'git merge ' still catches a real merge",
      verdict({"type": "tool_used", "tool": "Bash", "input_match": "git merge ", "max": 0},
              ctx(REAL_MERGE)),
      "fail")

check("grader: tool_order in the right order",
      verdict({"type": "tool_order",
               "before": {"tool": "Skill", "input_match": "devflow:flow"},
               "after": {"tool": "Bash", "input_match": "npm test"}}),
      "pass")

check("grader: tool_order in the wrong order",
      verdict({"type": "tool_order",
               "before": {"tool": "Bash", "input_match": "npm test"},
               "after": {"tool": "Skill", "input_match": "devflow:flow"}}),
      "fail")

check("grader: tool_order fails when one side never happened",
      verdict({"type": "tool_order",
               "before": {"tool": "Skill", "input_match": "devflow:flow"},
               "after": {"tool": "Skill", "input_match": "devflow:ship"}}),
      "fail")

check("grader: regex contains",
      verdict({"type": "regex", "target": "trace",
               "pattern": "Standard\\s*[—–-]", "match": "contains"}),
      "pass")

check("grader: regex not_contains passes when absent",
      verdict({"type": "regex", "target": "trace",
               "pattern": "Quick\\s*[—–-]", "match": "not_contains"}),
      "pass")

check("grader: regex on what was said finds the assistant's text",
      verdict({"type": "regex", "name": "x", "target": "said",
               "pattern": "Standard — changing", "match": "contains"}), "pass")
check("grader: regex on what was said ignores tool output",
      verdict({"type": "regex", "name": "x", "target": "said",
               "pattern": "# pass 4", "match": "contains"}), "fail")
check("grader: regex on what was said ignores the commands the run typed",
      verdict({"type": "regex", "name": "x", "target": "said",
               "pattern": "npm test", "match": "contains"}), "fail")
check("grader: regex not_contains fails when present",
      verdict({"type": "regex", "target": "trace",
               "pattern": "Standard\\s*[—–-]", "match": "not_contains"}),
      "fail")

with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, "CLAUDE.md"), "w").write("## Checks\n- Test: npm test\n")
    file_target = {"source": "file", "path": "CLAUDE.md"}
    check("grader: regex against a file the run wrote",
          verdict({"type": "regex", "target": file_target,
                   "pattern": "##\\s*Checks", "match": "contains"}, ctx(workdir=tmp)),
          "pass")
    check("grader: regex not_contains against a file",
          verdict({"type": "regex", "target": file_target,
                   "pattern": "Typecheck:", "match": "not_contains"}, ctx(workdir=tmp)),
          "pass")
    check("grader: a missing file fails contains, it does not skip",
          verdict({"type": "regex", "target": {"source": "file", "path": "gone.md"},
                   "pattern": "x", "match": "contains"}, ctx(workdir=tmp)),
          "fail")

with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, "there.txt"), "w").write("x")
    check("grader: file_exists true",
          verdict({"type": "file_exists", "path": "there.txt", "exists": True}, ctx(workdir=tmp)),
          "pass")
    check("grader: file_exists false when it is missing",
          verdict({"type": "file_exists", "path": "gone.txt", "exists": True}, ctx(workdir=tmp)),
          "fail")
    check("grader: file_exists inverted",
          verdict({"type": "file_exists", "path": "gone.txt", "exists": False}, ctx(workdir=tmp)),
          "pass")

# The load-bearing one. An llm grader is not scored here, and it must never be
# reported as a pass. `skip` and `pass` are different answers, the same way
# NOT RUN and none are.
check("grader: an llm grader is skipped, never passed",
      verdict({"type": "llm", "name": "x", "criteria": "anything"}),
      "skip")

check("grader: an unknown grader type is skipped, not passed",
      verdict({"type": "invented-later", "name": "x"}),
      "skip")

# ------------------------------------------- the README's line-number citations

# `evals/README.md` cites two lines of `skills/flow/SKILL.md` by number, to say
# why a rendered skill body is not trace. A line number is the one kind of
# citation that rots silently: the prose still reads correctly after the skill
# it points into has moved under it.

_FLOW_SKILL = os.path.join(os.path.dirname(HERE), "skills", "flow", "SKILL.md")


def squash(s):
    """One line, single-spaced -- a citation may wrap in the markdown source."""
    return " ".join(s.split())


with io.open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    _readme = f.read()
with io.open(_FLOW_SKILL, encoding="utf-8") as f:
    _flow_lines = f.read().split("\n")

CITATIONS = re.findall(r"`([^`]+)`\s+at (?:line )?(\d+)", _readme)

check("readme: both worked-example citations are found", len(CITATIONS), 2)

for _text, _num in CITATIONS:
    _n = int(_num)
    _line = _flow_lines[_n - 1] if 0 < _n <= len(_flow_lines) else ""
    check(
        "readme: skills/flow/SKILL.md line %s is the cited example" % _num,
        squash(_line),
        squash(_text),
    )

# The README's table says what breaks when a case fails. `deep-coordinator`
# now measures the chain loop, so its row has to name what a failure costs
# there, not the one-builder-per-piece loop it replaced.
_deep_rows = [l for l in _readme.split("\n") if l.startswith("| `deep-coordinator`")]
check("readme: the deep-coordinator row is there", len(_deep_rows), 1)
check_true(
    "readme: its row says what breaks in the chain loop",
    "chain" in (_deep_rows[0].lower() if _deep_rows else ""),
)

# ---------------------------------------- ship's conflict handoff has a case
#
# The handoff added to `ship` step 2 on 23 Sep 2026 branches four ways and
# every branch is load-bearing: hand over a lone conflict, once and never in a
# loop, re-read all four conditions on the way back, and never read an UNKNOWN
# mergeability as clearance. `skills/test-frontmatter.py` pins that the words
# are in the file. It cannot pin that a model follows them, and this repo has
# already paid to learn those are different things -- `worktree-guard` measured
# a correct instruction landing in 2 runs of 4.
#
# It is `manual: true`, and unavoidably so. `evals/fixtures/greeter.sh` builds a
# bare repo with no host, so `gh` errors there and `ship` stops at step 1 with
# nothing measured. A CONFLICTING pull request needs a real forge: a real
# branch, a real PR, and a real commit landing on the default branch underneath
# it. `plans-on-tracker` is the precedent and the shape is copied from it.
_SHIP_CASE = os.path.join(HERE, "ship-tends-conflict", "case.yaml")

check_true("ship-tends-conflict: the case exists", os.path.isfile(_SHIP_CASE))

if os.path.isfile(_SHIP_CASE):
    with io.open(_SHIP_CASE, encoding="utf-8") as f:
        _ship_case = run.parse_yaml(f.read())

    # Not a preference. Without it the case joins the default run, where it
    # fails for every user who has no DEVFLOW_EVAL_REPO set -- a red suite that
    # reports nothing about the skill, which is worse than no case at all.
    check("ship-tends-conflict: is manual, because no scaffold can fake a forge",
          _ship_case.get("manual"), True)

    # The prompt has to start the skill the case is about. A case that reaches
    # `ship` by some other route measures whatever that route does instead.
    check_true("ship-tends-conflict: starts ship, not another skill",
               "/devflow:ship" in (_ship_case.get("execution") or {}).get("prompt", ""))

    # The handoff is the whole point, so the printed line is what separates a
    # run that handed over from one that stopped on the conflict the way step 2
    # did before this. Both are plausible model behaviour; only one is the rule.
    _ship_graders = " ".join(
        str(_g.get("pattern", "")) + " " + str(_g.get("criteria", ""))
        for _g in _ship_case.get("graders") or []
    )
    check_true("ship-tends-conflict: grades the handoff line, not just the outcome",
               "conflict\\*\\* handing #" in _ship_graders)

_ship_rows = [l for l in _readme.split("\n")
              if l.startswith("| `ship-tends-conflict`")]
check("readme: the ship-tends-conflict row is there", len(_ship_rows), 1)

# The grader counts in the prose rot the same silent way a line number does:
# add a grader to any case and the sentence still reads fine.
_scorable = 0
_total = 0
for _name in sorted(os.listdir(HERE)):
    _case_path = os.path.join(HERE, _name, "case.yaml")
    if not os.path.isfile(_case_path):
        continue
    with io.open(_case_path, encoding="utf-8") as f:
        _gs = run.parse_yaml(f.read())["graders"]
    _total += len(_gs)
    _scorable += sum(1 for _g in _gs if _g.get("type") in run.GRADERS)

_counted = re.search(r"scores \*\*(\d+) of the (\d+) graders\*\*", _readme)
check_true("readme: the grader-count sentence is there", _counted is not None)
check(
    "readme: the grader counts match the case files",
    [int(_counted.group(1)), int(_counted.group(2))] if _counted else None,
    [_scorable, _total],
)


# --------------------------------------------- sizing-deep asks in rounds
#
# Deep asks in popup rounds, or -- where there is no popup tool, which is every
# `claude -p` run -- in a numbered list. Either way every question carries a
# recommendation. The case grades that with two scorable regex graders so the
# runner can say pass or fail without a judge: one wants at least one question
# with a recommendation after it, the other forbids a question that reaches the
# next question (or the end) with none. The `llm` grader stays for the rest.
with open(os.path.join(HERE, "sizing-deep", "case.yaml")) as fh:
    sizing_deep = run.parse_yaml(fh.read())
_sd = {g["name"]: g for g in sizing_deep["graders"]}

check_true("sizing-deep: the asks-a-recommended-question grader is there",
           "asks-a-recommended-question" in _sd)
check_true("sizing-deep: the no-question-lacks-a-recommendation grader is there",
           "no-question-lacks-a-recommendation" in _sd)


def sizing_deep_passes(said, popup=None):
    """True when both scorable question graders pass on a run that said `said`
    and, if `popup` is a list of (question, [labels]), called AskUserQuestion."""
    blocks = [{"type": "text", "text": said}] if said else []
    if popup is not None:
        blocks.append({"type": "tool_use", "id": "q1", "name": "AskUserQuestion",
                       "input": {"questions": [
                           {"question": q, "header": "Ask",
                            "options": [{"label": l, "description": "d"} for l in labels],
                            "multiSelect": False}
                           for q, labels in popup]}})
    c = ctx([{"type": "assistant", "message": {"content": blocks}}])
    return all(
        verdict(_sd[n], c) == "pass"
        for n in ("asks-a-recommended-question", "no-question-lacks-a-recommendation")
        if n in _sd
    )


_ANNOUNCE = "Deep — a plugin system cannot be named in files up front.\n\n"

check("sizing-deep: a numbered list with a recommendation on each passes",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommended: a registry in src/styles.js\n"
          "2. Can a style be async? Recommended: no, keep it sync\n"),
      True)

check("sizing-deep: a popup whose every question leads with (Recommended) passes",
      sizing_deep_passes(_ANNOUNCE,
          popup=[("Where do styles register?", ["A registry (Recommended)", "A config file"]),
                 ("Can a style be async?", ["No (Recommended)", "Yes"])]),
      True)

check("sizing-deep: a numbered list with no recommendation fails",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register?\n2. Can a style be async?\n"),
      False)

check("sizing-deep: a numbered list where only the first has one fails",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommended: a registry\n"
          "2. Can a style be async?\n"),
      False)

check("sizing-deep: a popup question with no recommendation fails",
      sizing_deep_passes(_ANNOUNCE,
          popup=[("Where do styles register?", ["A registry (Recommended)", "A config file"]),
                 ("Can a style be async?", ["No", "Yes"])]),
      False)

check("sizing-deep: a run that asked nothing fails",
      sizing_deep_passes(_ANNOUNCE + "I will start building now."),
      False)

# A recommendation on the question's own line, before its "?", is still on
# that question. The question marker once swallowed the whole line up to the
# "?", so these failed a run that had recommended every time.
check("sizing-deep: a recommendation inside the question line passes",
      sizing_deep_passes(_ANNOUNCE +
          "1. Registry (Recommended) or a config file?\n"
          "2. Sync (Recommended) or async?\n"),
      True)

check("sizing-deep: a recommendation before a second ? on the line passes",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommend: a registry — fine?\n"),
      True)

check("sizing-deep: an inline one on the first does not cover the second",
      sizing_deep_passes(_ANNOUNCE +
          "1. Registry (Recommended) or a config file?\n"
          "2. Sync or async?\n"),
      False)

check("sizing-deep: a todo list without question marks is not read as questions",
      sizing_deep_passes(_ANNOUNCE +
          "1. add the registry\n2. add the loader\n"
          "3. Where do styles register? Recommended: a registry\n"),
      True)

# Issue #105: a model often writes the number in bold, and the marker wanted
# the line to start with the number, so it saw no question at all.
check("sizing-deep: a bold-numbered question with a recommendation passes",
      sizing_deep_passes(_ANNOUNCE +
          "**1. How does a user pick a style?**\n   → Recommend: a flag\n"),
      True)
check("sizing-deep: a bold-numbered question with none fails",
      sizing_deep_passes(_ANNOUNCE +
          "**1. How does a user pick a style?** Recommend: a flag\n"
          "**2. Can a style be async?**\n"),
      False)


def then_a_researcher(said):
    """Events for a run that said `said`, then started a researcher whose
    report says "recommended" -- ESLint's `eslint:recommended`, not a
    recommendation on any question."""
    return [
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": said},
            {"type": "tool_use", "id": "r1", "name": "Agent",
             "input": {"subagent_type": "devflow:researcher", "prompt": "q",
                       "description": "d"}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "r1",
             "content": "ESLint configs extend eslint:recommended."}]}},
    ]


# Issue #104: the trace holds what the researcher returned, so a question with
# no recommendation once borrowed the researcher's "recommended". The scan
# stops at the next tool call.
check("sizing-deep: a researcher's 'recommended' does not cover a question",
      verdict(_sd["no-question-lacks-a-recommendation"],
              ctx(then_a_researcher(_ANNOUNCE + "1. Should plugins be npm packages?\n"))),
      "fail")
check("sizing-deep: a recommended question before a researcher passes",
      verdict(_sd["no-question-lacks-a-recommendation"],
              ctx(then_a_researcher(_ANNOUNCE +
                  "1. Should plugins be npm packages? Recommended: yes\n"))),
      "pass")

# flow ends a numbered round with 'Reply "yes to all" to take every
# recommendation', so the last question once borrowed that line's word. Found
# re-grading a paid research-in-rounds trace with question 4's taken out.
_REPLY = '\nReply **"yes to all"** to take every recommendation.\n'
check("sizing-deep: the reply line does not cover the last question",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommended: a registry\n"
          "2. Can a style be async?\n" + _REPLY),
      False)
check("sizing-deep: every question recommended, then the reply line, passes",
      sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommended: a registry\n"
          "2. Can a style be async? Recommended: no\n" + _REPLY),
      True)
check("sizing-deep: a marked-up reply line does not cover the last one",
      [sizing_deep_passes(_ANNOUNCE +
          "1. Where do styles register? Recommended: a registry\n"
          "2. Can a style be async?\n" + reply)
       for reply in ('\n**Reply "yes to all" to take every recommendation.**\n',
                     '\n> Reply "yes to all" to take every recommendation.\n',
                     '\n*Reply "yes to all" to take every recommendation.*\n',
                     '\n_Reply "yes to all" to take every recommendation._\n',
                     '\n__Reply__ "yes to all" to take every recommendation.\n',
                     '\n- Reply "yes to all" to take every recommendation.\n')],
      [False] * 6)

# --------------------------------------- research-in-rounds starts a researcher
#
# Issue #92: on Deep, `flow` starts a `devflow:researcher` on its own when a
# question needs a fact nobody has read, and never asks whether to research.
# The case asks for plugins "the way ESLint loads its plugins" -- a fact outside
# the repo. Its graders are pinned both ways here, so none of them reads as
# coverage while being unable to fail.
_rr_path = os.path.join(HERE, "research-in-rounds", "case.yaml")
research_rounds = {}
if os.path.isfile(_rr_path):
    with open(_rr_path) as fh:
        research_rounds = run.parse_yaml(fh.read())
_rr = {g["name"]: g for g in research_rounds.get("graders", [])}

check_true("research-in-rounds: the case exists", research_rounds != {})
check_true("research-in-rounds: the prompt needs a fact from outside the repo",
           "ESLint" in research_rounds.get("execution", {}).get("prompt", ""))
check_true("research-in-rounds: Agent is allowed, or no researcher can start",
           "Agent" in research_rounds.get("execution", {}).get("allowed_tools", []))
for _n in ("announces-deep", "starts-a-researcher", "at-most-3-researchers",
           "never-asks-whether-to-research", "asks-a-recommended-question"):
    check_true("research-in-rounds: the %s grader is there" % _n, _n in _rr)


def research_rounds_verdict(name, said="", agents=()):
    """The verdict of one research-in-rounds grader on a run that said `said`
    and started one Agent per entry in `agents`, each a subagent_type."""
    if name not in _rr:
        return None
    blocks = [{"type": "text", "text": said}] if said else []
    for i, kind in enumerate(agents):
        blocks.append({"type": "tool_use", "id": "a%d" % i, "name": "Agent",
                       "input": {"subagent_type": kind, "prompt": "q",
                                 "description": "d"}})
    return verdict(_rr[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


_RR_SAID = ("Deep — a plugin system, files not nameable yet.\n\n"
            "1. Should plugins be npm packages? Recommended: yes\n")

check("research-in-rounds: one researcher passes starts-a-researcher",
      research_rounds_verdict("starts-a-researcher", _RR_SAID, ["devflow:researcher"]),
      "pass")
check("research-in-rounds: no agent fails starts-a-researcher",
      research_rounds_verdict("starts-a-researcher", _RR_SAID), "fail")
check("research-in-rounds: a builder is not a researcher",
      research_rounds_verdict("starts-a-researcher", _RR_SAID, ["devflow:builder"]),
      "fail")
check("research-in-rounds: 3 researchers is within the cap",
      research_rounds_verdict("at-most-3-researchers", _RR_SAID,
                              ["devflow:researcher"] * 3), "pass")
check("research-in-rounds: 4 researchers breaks the cap",
      research_rounds_verdict("at-most-3-researchers", _RR_SAID,
                              ["devflow:researcher"] * 4), "fail")
# The first paid run asked "**1. How does a user pick a style ...?**" with
# "→ Recommend:" under it, and the grader missed it: the bold marks sat
# before the number, where the question marker wanted the line to start.
check("research-in-rounds: a bold-numbered question with a recommendation passes",
      research_rounds_verdict("asks-a-recommended-question",
          "**1. How does a user pick a style when they run the CLI?**\n"
          "   → Recommend: a `--style <name>` flag\n"), "pass")
check("research-in-rounds: a bold-numbered question with none still fails",
      research_rounds_verdict("asks-a-recommended-question",
          "**1. How does a user pick a style when they run the CLI?**\n"), "fail")

check("research-in-rounds: plain questions do not ask whether to research",
      research_rounds_verdict("never-asks-whether-to-research", _RR_SAID), "pass")
check("research-in-rounds: 'Should I research ... first?' is caught",
      research_rounds_verdict("never-asks-whether-to-research", _RR_SAID +
          "2. Should I research how ESLint loads plugins first? Recommended: yes\n"),
      "fail")
check("research-in-rounds: 'Would you like me to research' is caught",
      research_rounds_verdict("never-asks-whether-to-research",
          "Would you like me to research how ESLint loads plugins?"), "fail")
check("research-in-rounds: a 'Research first (Recommended)' option is caught",
      research_rounds_verdict("never-asks-whether-to-research",
          '"label": "Research first (Recommended)"'), "fail")
check_true("research-in-rounds: the no-question-lacks-a-recommendation grader is there",
      "no-question-lacks-a-recommendation" in _rr)
check("research-in-rounds: a question with no recommendation fails, even with one later",
      research_rounds_verdict("no-question-lacks-a-recommendation",
          "1. Should plugins be npm packages?\n"
          "2. Where do they live? Recommended: node_modules\n"), "fail")
check("research-in-rounds: bold-numbered questions, each recommended, pass",
      research_rounds_verdict("no-question-lacks-a-recommendation",
          "**1. How does a user pick a style?**\n   → Recommend: a flag\n"
          "**2. Where do plugins live?**\n   → Recommend: node_modules\n"), "pass")
check("research-in-rounds: 'Do you want me to research' is caught",
      research_rounds_verdict("never-asks-whether-to-research",
          "Do you want me to research ESLint's loader before we go on?"),
      "fail")
check("research-in-rounds: a researcher's 'recommended' does not cover a question",
      verdict(_rr["no-question-lacks-a-recommendation"],
              ctx(then_a_researcher("1. Should plugins be npm packages?\n"))),
      "fail")
check("research-in-rounds: a recommended question before a researcher passes",
      verdict(_rr["no-question-lacks-a-recommendation"],
              ctx(then_a_researcher(_RR_SAID))),
      "pass")
check("research-in-rounds: the reply line does not cover the last question",
      research_rounds_verdict("no-question-lacks-a-recommendation",
          _RR_SAID + "2. Where do they live?\n" + _REPLY), "fail")
check("research-in-rounds: every question recommended, then the reply line, passes",
      research_rounds_verdict("no-question-lacks-a-recommendation",
          _RR_SAID + "2. Where do they live? Recommended: node_modules\n" + _REPLY),
      "pass")
# A popup's questions sit on one line of JSON, so the stop at the next tool
# call must not cut a popup's own recommendation off.
check("research-in-rounds: a recommended popup before a researcher passes",
      verdict(_rr["no-question-lacks-a-recommendation"],
              ctx([{"type": "assistant", "message": {"content": [
                  {"type": "tool_use", "id": "q1", "name": "AskUserQuestion",
                   "input": {"questions": [
                       {"question": "Should plugins be npm packages?",
                        "options": [{"label": "Yes (Recommended)"}, {"label": "No"}]}]}}]}}]
                  + then_a_researcher("Starting a researcher.\n"))),
      "pass")
check("research-in-rounds: an unrecommended popup before a researcher fails",
      verdict(_rr["no-question-lacks-a-recommendation"],
              ctx([{"type": "assistant", "message": {"content": [
                  {"type": "tool_use", "id": "q1", "name": "AskUserQuestion",
                   "input": {"questions": [
                       {"question": "Should plugins be npm packages?",
                        "options": [{"label": "Yes"}, {"label": "No"}]}]}}]}}]
                  + then_a_researcher("Starting a researcher.\n"))),
      "fail")

# --------------------------------------- discuss-trigger starts discuss, then a researcher
#
# Issue #101: a request to discuss a design, typed with no slash command, starts
# `devflow:discuss` and, for a fact outside the repo, a `devflow:researcher`.
# Pinned both ways, so no grader reads as coverage while unable to fail.
_dt_path = os.path.join(HERE, "discuss-trigger", "case.yaml")
discuss_trigger = {}
if os.path.isfile(_dt_path):
    with open(_dt_path) as fh:
        discuss_trigger = run.parse_yaml(fh.read())
_dt = {g["name"]: g for g in discuss_trigger.get("graders", [])}

check_true("discuss-trigger: the case exists", discuss_trigger != {})
_dt_prompt = discuss_trigger.get("execution", {}).get("prompt", "")
check_true("discuss-trigger: the prompt names no slash command", "/devflow" not in _dt_prompt)
check_true("discuss-trigger: the prompt asks what other tools do", "other CLIs" in _dt_prompt)
check_true("discuss-trigger: Agent is allowed, or no researcher can start",
           "Agent" in discuss_trigger.get("execution", {}).get("allowed_tools", []))
for _n in ("reaches-discuss-unprompted", "starts-a-researcher", "edits-no-file",
           "writes-no-file"):
    check_true("discuss-trigger: the %s grader is there" % _n, _n in _dt)


def discuss_trigger_verdict(name, calls=()):
    """The verdict of one discuss-trigger grader on a run that made `calls`,
    each a (tool, input) pair."""
    if name not in _dt:
        return None
    blocks = [{"type": "tool_use", "id": "t%d" % i, "name": tool, "input": inp}
              for i, (tool, inp) in enumerate(calls)]
    return verdict(_dt[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


_DT_SKILL = ("Skill", {"skill": "devflow:discuss"})
_DT_RESEARCHER = ("Agent", {"subagent_type": "devflow:researcher", "prompt": "q",
                            "description": "d"})

check("discuss-trigger: a Skill call to discuss passes reaches-discuss-unprompted",
      discuss_trigger_verdict("reaches-discuss-unprompted", [_DT_SKILL]), "pass")
check("discuss-trigger: no Skill call fails reaches-discuss-unprompted",
      discuss_trigger_verdict("reaches-discuss-unprompted", [_DT_RESEARCHER]), "fail")
check("discuss-trigger: flow is not discuss",
      discuss_trigger_verdict("reaches-discuss-unprompted",
                              [("Skill", {"skill": "devflow:flow"})]), "fail")
check("discuss-trigger: a researcher Agent call passes starts-a-researcher",
      discuss_trigger_verdict("starts-a-researcher", [_DT_SKILL, _DT_RESEARCHER]), "pass")
check("discuss-trigger: no agent fails starts-a-researcher",
      discuss_trigger_verdict("starts-a-researcher", [_DT_SKILL]), "fail")
check("discuss-trigger: a builder is not a researcher",
      discuss_trigger_verdict("starts-a-researcher",
          [("Agent", {"subagent_type": "devflow:builder", "prompt": "q"})]), "fail")
check("discuss-trigger: a run that edits nothing passes edits-no-file",
      discuss_trigger_verdict("edits-no-file", [_DT_SKILL, _DT_RESEARCHER]), "pass")
check("discuss-trigger: an Edit fails edits-no-file",
      discuss_trigger_verdict("edits-no-file",
          [("Edit", {"file_path": "README.md", "old_string": "a", "new_string": "b"})]),
      "fail")
check("discuss-trigger: a Write fails writes-no-file",
      discuss_trigger_verdict("writes-no-file",
          [("Write", {"file_path": "config.md", "content": "x"})]), "fail")

# ----------------------------- sweep-quick-issues: one PR per chain, no questions
#
# `sweep` opens many PRs from one run and its sweepers cannot ask. The case needs
# a real GitHub repo with real issues, so it is manual like `plans-on-tracker`.
# Four issues: two that share a file (one chain), one on its own (a second
# chain), one that is not Quick (skipped). Pinned both ways, so no grader reads
# as coverage while unable to fail.
_sw_path = os.path.join(HERE, "sweep-quick-issues", "case.yaml")
sweep_case = {}
if os.path.isfile(_sw_path):
    with open(_sw_path) as fh:
        sweep_case = run.parse_yaml(fh.read())
_sw = {g["name"]: g for g in sweep_case.get("graders", [])}
_sw_ex = sweep_case.get("execution", {})

check_true("sweep-quick-issues: the case exists", sweep_case != {})
check("sweep-quick-issues: is manual, because it needs a real repo with real issues",
      sweep_case.get("manual"), True)
check_true("sweep-quick-issues: starts sweep, not another skill",
           "/devflow:sweep" in _sw_ex.get("prompt", ""))
check_true("sweep-quick-issues: the prompt tells the run not to wait",
           "do not wait" in _sw_ex.get("prompt", ""))
check_true("sweep-quick-issues: Agent is allowed, or no sweeper can start",
           {"Agent", "Skill", "Bash"} <= set(_sw_ex.get("allowed_tools", [])))
for _n in ("prints-the-chain-list", "starts-one-sweeper-per-chain",
           "opens-one-pr-per-chain", "never-starts-the-not-quick-issue",
           "prints-the-skipped-line", "asks-no-question", "comments-on-no-issue",
           "one-pr-closes-the-shared-file-issues"):
    check_true("sweep-quick-issues: the %s grader is there" % _n, _n in _sw)

_sw_scaffold = os.path.join(HERE, "sweep-quick-issues", "scaffold.sh")
_sw_scaffold_text = ""
if os.path.isfile(_sw_scaffold):
    with open(_sw_scaffold) as fh:
        _sw_scaffold_text = fh.read()
check("sweep-quick-issues: the scaffold opens 4 issues through REST",
      len(re.findall(r'^open_issue "', _sw_scaffold_text, re.M)), 4)
check_true("sweep-quick-issues: the scaffold writes the issue numbers for the prompt",
           ".sweep-issues" in _sw_scaffold_text
           and ".sweep-issues" in _sw_ex.get("prompt", ""))
_sw_rows = [l for l in _readme.split("\n") if l.startswith("| `sweep-quick-issues`")]
check("readme: the sweep-quick-issues row is there", len(_sw_rows), 1)
check_true("readme: its row says it is manual",
           len(_sw_rows) == 1 and "**manual**" in _sw_rows[0])
check_true("sweep-quick-issues: the scaffold never runs a GraphQL issue command",
           _sw_scaffold_text != "" and re.search(r"gh issue ", _sw_scaffold_text) is None)
check_true("sweep-quick-issues: the scaffold names the repo from DEVFLOW_EVAL_REPO",
           "DEVFLOW_EVAL_REPO" in _sw_scaffold_text)


def sweep_verdict(name, calls=(), said=""):
    """The verdict of one sweep-quick-issues grader on a run that said `said`
    and made `calls`, each a (tool, input) pair."""
    if name not in _sw:
        return None
    blocks = [{"type": "tool_use", "id": "t%d" % i, "name": tool, "input": inp}
              for i, (tool, inp) in enumerate(calls)]
    if said:
        blocks.append({"type": "text", "text": said})
    return verdict(_sw[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


def _sweeper(prompt):
    return ("Agent", {"subagent_type": "devflow:sweeper", "prompt": prompt,
                      "description": "d", "isolation": "worktree"})


def _open_pr(title):
    return ("Bash", {"command": "gh api repos/{owner}/{repo}/pulls -f title=\"%s\" "
                                "-F body=@/tmp/b -f head=x -f base=main" % title})


_SW_NOT_QUICK = "Rework the greeting across every module"

check("sweep-quick-issues: the right list line passes prints-the-chain-list",
      sweep_verdict("prints-the-chain-list",
                    said="→ **sweep** 3 issues in 2 chains, 1 skipped"), "pass")
# Live test 1 printed the list inside a code block, where the bold markers
# were dropped: "→ sweep 3 issues in 2 chains, 1 skipped". The count is what
# the grader is for, so the plain line passes too.
check("sweep-quick-issues: the list line without bold passes prints-the-chain-list",
      sweep_verdict("prints-the-chain-list",
                    said="→ sweep 3 issues in 2 chains, 1 skipped"), "pass")
check("sweep-quick-issues: one chain for three issues fails prints-the-chain-list",
      sweep_verdict("prints-the-chain-list",
                    said="→ **sweep** 3 issues in 1 chains, 1 skipped"), "fail")
check("sweep-quick-issues: two sweepers pass starts-one-sweeper-per-chain",
      sweep_verdict("starts-one-sweeper-per-chain",
                    [_sweeper("#1 #2"), _sweeper("#3")]), "pass")
check("sweep-quick-issues: one sweeper per issue fails starts-one-sweeper-per-chain",
      sweep_verdict("starts-one-sweeper-per-chain",
                    [_sweeper("#1"), _sweeper("#2"), _sweeper("#3")]), "fail")
check("sweep-quick-issues: a builder is not a sweeper",
      sweep_verdict("starts-one-sweeper-per-chain",
                    [("Agent", {"subagent_type": "devflow:builder", "prompt": "x"}),
                     ("Agent", {"subagent_type": "devflow:builder", "prompt": "y"})]),
      "fail")
check("sweep-quick-issues: two PRs pass opens-one-pr-per-chain",
      sweep_verdict("opens-one-pr-per-chain", [_open_pr("a"), _open_pr("b")]), "pass")
check("sweep-quick-issues: three PRs fail opens-one-pr-per-chain",
      sweep_verdict("opens-one-pr-per-chain",
                    [_open_pr("a"), _open_pr("b"), _open_pr("c")]), "fail")
check("sweep-quick-issues: one PR fails opens-one-pr-per-chain",
      sweep_verdict("opens-one-pr-per-chain", [_open_pr("a")]), "fail")
check("sweep-quick-issues: a sweeper on the not-Quick issue fails the skip",
      sweep_verdict("never-starts-the-not-quick-issue",
                    [_sweeper("#4 " + _SW_NOT_QUICK)]), "fail")
check("sweep-quick-issues: sweepers on the Quick issues pass the skip",
      sweep_verdict("never-starts-the-not-quick-issue",
                    [_sweeper("#1 #2"), _sweeper("#3")]), "pass")
check("sweep-quick-issues: a skipped line passes prints-the-skipped-line",
      sweep_verdict("prints-the-skipped-line",
                    said="– skipped #4 not Quick, reaches many files"), "pass")
check("sweep-quick-issues: the Done report's skipped line passes too",
      sweep_verdict("prints-the-skipped-line",
                    said="– **skipped** #4 not Quick"), "pass")
check("sweep-quick-issues: no skipped line fails prints-the-skipped-line",
      sweep_verdict("prints-the-skipped-line", said="all done"), "fail")
check("sweep-quick-issues: a question fails asks-no-question",
      sweep_verdict("asks-no-question",
                    [("AskUserQuestion", {"questions": []})]), "fail")
check("sweep-quick-issues: no question passes asks-no-question",
      sweep_verdict("asks-no-question", [_sweeper("#1")]), "pass")
check("sweep-quick-issues: a comment on an issue fails comments-on-no-issue",
      sweep_verdict("comments-on-no-issue",
                    [("Bash", {"command": "gh api repos/o/r/issues/4/comments -f body=x"})]),
      "fail")

# ------------------------------------- setup and direct mode have their cases
#
# `setup` became a questionnaire that writes `## Workflow`, and a direct
# project commits on main with no branch and no review for Quick work. Both
# are promises between skills that a pin on the file cannot keep. Nothing
# here calls a model: the graders are fed transcripts built by hand, one that
# does the right thing and one that does not.

with open(os.path.join(HERE, "setup-writes-checks", "case.yaml")) as fh:
    _setup_case = run.parse_yaml(fh.read())
_su = {g["name"]: g for g in _setup_case["graders"]}


def _workflow_file_verdict(claude_md):
    """The writes-workflow-block verdict on a CLAUDE.md with this content."""
    if "writes-workflow-block" not in _su:
        return None
    _d = tempfile.mkdtemp()
    try:
        with open(os.path.join(_d, "CLAUDE.md"), "w") as fh:
            fh.write(claude_md)
        return verdict(_su["writes-workflow-block"], ctx(workdir=_d))
    finally:
        shutil.rmtree(_d, ignore_errors=True)


check("setup-writes-checks: a Workflow block with Mode: direct passes",
      _workflow_file_verdict("## Checks\n- Test: npm test\n\n## Workflow\n"
                             "- Mode: direct\n- About: a greeter\n"), "pass")
check("setup-writes-checks: a Workflow block with Mode: pr passes",
      _workflow_file_verdict("## Workflow\n- Mode: pr\n- About: x\n"), "pass")
check("setup-writes-checks: no Workflow block fails",
      _workflow_file_verdict("## Checks\n- Test: npm test\n"), "fail")
check("setup-writes-checks: a Mode that is neither direct nor pr fails",
      _workflow_file_verdict("## Workflow\n- Mode: both\n"), "fail")
check_true("setup-writes-checks: the Checks graders are still there",
           {"has-checks-block", "records-test-command", "records-lint-command",
            "invents-no-typecheck", "actually-ran-the-test-command",
            "actually-ran-the-lint-command"} <= set(_su))
# Nobody is at the keyboard in a scored run, so the prompt has to say yes to
# the questionnaire, the way worktree-guard does for flow's.
check_true("setup-writes-checks: the prompt answers the questionnaire itself",
           "yes to all" in _setup_case["execution"]["prompt"])

_dm_case_path = os.path.join(HERE, "direct-mode", "case.yaml")
check_true("direct-mode: the case exists", os.path.isfile(_dm_case_path))
_dm = {}
_dm_case = {}
if os.path.isfile(_dm_case_path):
    with open(_dm_case_path) as fh:
        _dm_case = run.parse_yaml(fh.read())
    _dm = {g["name"]: g for g in _dm_case["graders"]}
check_true("direct-mode: the prompt is a Quick change through flow",
           "/devflow:flow" in _dm_case.get("execution", {}).get("prompt", ""))


def dm_verdict(name, calls=(), said=""):
    """The verdict of one direct-mode grader on a run that made `calls`, each a
    (tool, input) pair, and said `said`."""
    if name not in _dm:
        return None
    blocks = [{"type": "tool_use", "id": "d%d" % i, "name": tool, "input": inp}
              for i, (tool, inp) in enumerate(calls)]
    if said:
        blocks.append({"type": "text", "text": said})
    return verdict(_dm[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


_DM_COMMIT = ("Bash", {"command": "git commit -am 'docs: fix typo'"})
_DM_BRANCH = ("Bash", {"command": "git checkout -b docs/typo main"})
_DM_SWITCH = ("Bash", {"command": "git switch -c docs/typo"})
_DM_REVIEW_AGENT = ("Agent", {"subagent_type": "devflow:reviewer", "prompt": "p"})
_DM_REVIEW_SKILL = ("Skill", {"skill": "devflow:review", "args": "abc123"})

check("direct-mode: a run that never cuts a branch passes",
      dm_verdict("cuts-no-branch", [_DM_COMMIT]), "pass")
check("direct-mode: checkout -b fails cuts-no-branch",
      dm_verdict("cuts-no-branch", [_DM_BRANCH, _DM_COMMIT]), "fail")
check("direct-mode: switch -c fails cuts-no-branch",
      dm_verdict("cuts-no-branch", [_DM_SWITCH, _DM_COMMIT]), "fail")
check("direct-mode: a commit passes commits-on-main",
      dm_verdict("commits-on-main", [_DM_COMMIT]), "pass")
check("direct-mode: no commit fails commits-on-main",
      dm_verdict("commits-on-main", []), "fail")
check("direct-mode: no reviewer agent passes starts-no-review-agent",
      dm_verdict("starts-no-review-agent", [_DM_COMMIT]), "pass")
check("direct-mode: a reviewer agent fails starts-no-review-agent",
      dm_verdict("starts-no-review-agent", [_DM_REVIEW_AGENT]), "fail")
check("direct-mode: calling devflow:review fails calls-no-review",
      dm_verdict("calls-no-review", [_DM_REVIEW_SKILL]), "fail")
check("direct-mode: no review call passes calls-no-review",
      dm_verdict("calls-no-review", [_DM_COMMIT]), "pass")
check("direct-mode: the skipped line passes prints-review-skipped",
      dm_verdict("prints-review-skipped",
                 said="– **review** skipped — Quick, direct mode"), "pass")
check("direct-mode: a dash-tolerant skipped line passes prints-review-skipped",
      dm_verdict("prints-review-skipped",
                 said="- **review** skipped - Quick, direct mode"), "pass")
check("direct-mode: no skipped line fails prints-review-skipped",
      dm_verdict("prints-review-skipped", said="✓ **review** all three ran"), "fail")

_dm_scaffold = os.path.join(HERE, "direct-mode", "scaffold.sh")
check_true("direct-mode: the scaffold exists", os.path.isfile(_dm_scaffold))

# The real scaffold runs beside a stub greeter.sh that builds a repo with a
# remote, as the real one does: the real one runs npm and node, and this test
# needs python3 and git alone. What the scaffold has to leave behind is a
# project that says direct, has no remote, and starts with a clean tree on main.
if os.path.isfile(_dm_scaffold):
    _tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(_tmp, "case"))
        os.makedirs(os.path.join(_tmp, "fixtures"))
        shutil.copy(_dm_scaffold, os.path.join(_tmp, "case", "scaffold.sh"))
        with open(os.path.join(_tmp, "fixtures", "greeter.sh"), "w") as fh:
            fh.write(
                '#!/usr/bin/env bash\nset -e\nmkdir -p "$1"\ncd "$1"\n'
                'git init -q -b main\ngit config user.email e@x\n'
                'git config user.name e\ngit config commit.gpgsign false\n'
                'printf "## Checks\\n- Test: npm test\\n\\n## Workflow\\n'
                '- Mode: pr\\n- About: a tiny CLI\\n" > CLAUDE.md\n'
                'printf "# greeter\\n\\nA tiny CLI that says hello.\\n" > README.md\n'
                'git add -A\ngit commit -qm init\n'
                'git init -q --bare "$1.origin.git"\n'
                'git remote add origin "$1.origin.git"\n')
        os.chmod(os.path.join(_tmp, "fixtures", "greeter.sh"), 0o755)
        _ws = os.path.join(_tmp, "ws")
        _sc = subprocess.run(["bash", os.path.join(_tmp, "case", "scaffold.sh"), _ws],
                             capture_output=True, text=True)
        check("direct-mode: the scaffold exits 0", _sc.returncode, 0)

        def _git(*args):
            return subprocess.run(["git"] + list(args), cwd=_ws,
                                  capture_output=True, text=True).stdout.strip()

        _md = ""
        if os.path.isfile(os.path.join(_ws, "CLAUDE.md")):
            with open(os.path.join(_ws, "CLAUDE.md")) as fh:
                _md = fh.read()
        check_true("direct-mode: CLAUDE.md keeps ## Checks", "## Checks" in _md)
        check_true("direct-mode: CLAUDE.md says ## Workflow, Mode: direct",
                   re.search(r"## Workflow\n- Mode: direct\n", _md))
        # The shared fixture writes a pr block; this case swaps it, never adds a
        # second one, or a skill reading the first block would see pr.
        check("direct-mode: CLAUDE.md has one ## Workflow block, not two",
              _md.count("## Workflow"), 1)
        check_true("direct-mode: the fixture's Mode: pr is gone", "- Mode: pr" not in _md)
        check("direct-mode: the project has no remote", _git("remote"), "")
        check("direct-mode: it starts on main", _git("rev-parse", "--abbrev-ref", "HEAD"), "main")
        check("direct-mode: it starts with a clean tree", _git("status", "--porcelain"), "")
        check_true("direct-mode: the typo is in the README", "sasy hello" in
                   open(os.path.join(_ws, "README.md")).read())
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)

# The README row is what a reader checks to learn what a failure costs.
_dm_rows = [l for l in _readme.split("\n") if l.startswith("| `direct-mode`")]
check("readme: the direct-mode row is there", len(_dm_rows), 1)

# flow calls setup first when CLAUDE.md has no `## Workflow` block. A fixture
# that writes `## Checks` alone would send every case through setup's
# questionnaire before the thing it measures. Only setup-writes-checks starts
# with no CLAUDE.md at all, on purpose.
_EVALS = os.path.dirname(os.path.abspath(__file__))
for _rel in ["fixtures/greeter.sh", "plans-on-tracker/scaffold.sh",
             "ship-tends-conflict/scaffold.sh", "sweep-quick-issues/scaffold.sh"]:
    with open(os.path.join(_EVALS, _rel)) as fh:
        _src = fh.read()
    check_true(f"{_rel}: writes ## Checks", "## Checks" in _src)
    check_true(f"{_rel}: writes ## Workflow with Mode: pr beside it, so flow skips setup",
               re.search(r"## Workflow\n- Mode: pr\n- About: ", _src))
# ----------------------- skills-suggests-railway: names the vendor, installs nothing
#
# Issue #91: `/devflow:skills` on a repo with a railway.json suggests the
# Railway plugin, prints the project-scope command, and runs no install: the
# human runs it. Bash stays allowed on purpose, so "runs no install" can fail.
# Pinned both ways, so no grader reads as coverage while unable to fail.
_sr_path = os.path.join(HERE, "skills-suggests-railway", "case.yaml")
railway_case = {}
if os.path.isfile(_sr_path):
    with open(_sr_path) as fh:
        railway_case = run.parse_yaml(fh.read())
_sr = {g["name"]: g for g in railway_case.get("graders", [])}
_sr_ex = railway_case.get("execution", {})

check_true("skills-suggests-railway: the case exists", railway_case != {})
check("skills-suggests-railway: runs once, because it is cheap and one run is the bar",
      railway_case.get("runs"), 1)
check_true("skills-suggests-railway: starts the skills skill",
           "/devflow:skills" in _sr_ex.get("prompt", ""))
check_true("skills-suggests-railway: Bash is allowed, or an install could never fail it",
           {"Bash", "Skill"} <= set(_sr_ex.get("allowed_tools", [])))
for _n in ("names-the-railway-repo", "prints-project-scope",
           "runs-no-plugin-install", "runs-no-marketplace-add",
           "runs-no-skills-add", "suggests-no-mcp-only-install"):
    check_true("skills-suggests-railway: the %s grader is there" % _n, _n in _sr)

_sr_scaffold = os.path.join(HERE, "skills-suggests-railway", "scaffold.sh")
_sr_scaffold_text = ""
if os.path.isfile(_sr_scaffold):
    with open(_sr_scaffold) as fh:
        _sr_scaffold_text = fh.read()
check_true("skills-suggests-railway: the scaffold writes a railway.json and commits it",
           "railway.json" in _sr_scaffold_text and "git commit" in _sr_scaffold_text)
check_true("skills-suggests-railway: the scaffold starts from the shared package.json fixture",
           "greeter.sh" in _sr_scaffold_text)


def railway_verdict(name, text="", calls=()):
    """The verdict of one skills-suggests-railway grader on a run that said
    `text` and made `calls`, each a (tool, input) pair."""
    if name not in _sr:
        return None
    blocks = [{"type": "text", "text": text}] + [
        {"type": "tool_use", "id": "t%d" % i, "name": tool, "input": inp}
        for i, (tool, inp) in enumerate(calls)]
    return verdict(_sr[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


_SR_REPLY = ("Railway: claude plugin marketplace add railwayapp/railway-skills "
             "--scope project, then claude plugin install railway@railway-skills "
             "--scope project")
check("skills-suggests-railway: a reply naming the repo passes names-the-railway-repo",
      railway_verdict("names-the-railway-repo", _SR_REPLY), "pass")
check("skills-suggests-railway: a reply without it fails names-the-railway-repo",
      railway_verdict("names-the-railway-repo", "Nothing fits this repo."), "fail")
check("skills-suggests-railway: a reply with --scope project passes prints-project-scope",
      railway_verdict("prints-project-scope", _SR_REPLY), "pass")
check("skills-suggests-railway: a reply without it fails prints-project-scope",
      railway_verdict("prints-project-scope", "Install railway-skills."), "fail")
check("skills-suggests-railway: a run that only prints passes runs-no-plugin-install",
      railway_verdict("runs-no-plugin-install", _SR_REPLY,
                      [("Bash", {"command": "claude plugin list --json"})]), "pass")
check("skills-suggests-railway: running claude plugin install fails runs-no-plugin-install",
      railway_verdict("runs-no-plugin-install", _SR_REPLY,
          [("Bash", {"command": "claude plugin install railway@railway-skills --scope project"})]),
      "fail")
check("skills-suggests-railway: running marketplace add fails runs-no-marketplace-add",
      railway_verdict("runs-no-marketplace-add", _SR_REPLY,
          [("Bash", {"command": "claude plugin marketplace add railwayapp/railway-skills --scope project"})]),
      "fail")
check("skills-suggests-railway: running npx skills add fails runs-no-skills-add",
      railway_verdict("runs-no-skills-add", _SR_REPLY,
          [("Bash", {"command": "npx skills add railwayapp/railway-skills"})]), "fail")
check("skills-suggests-railway: npx skills find is not an install",
      railway_verdict("runs-no-skills-add", _SR_REPLY,
          [("Bash", {"command": "DISABLE_TELEMETRY=1 npx skills find railway"})]), "pass")
check("skills-suggests-railway: printing the MCP-only line too fails suggests-no-mcp-only-install",
      railway_verdict("suggests-no-mcp-only-install",
          _SR_REPLY + " Or: claude mcp add railway --transport http https://mcp.railway.com"),
      "fail")
check("skills-suggests-railway: the plugin alone passes suggests-no-mcp-only-install",
      railway_verdict("suggests-no-mcp-only-install", _SR_REPLY), "pass")

# The vendor table holds both the repo name and the MCP-only line, and a run
# may `cat` or grep it: Bash and Grep results stay in the trace. Every install
# line there carries `--scope project` too. So all three text graders read
# only what the run said, or that read decides them.
_SR_CAT = [
    {"type": "assistant", "message": {"content": [
        {"type": "text", "text": "Nothing fits this repo."},
        {"type": "tool_use", "id": "c1", "name": "Bash",
         "input": {"command": "cat skills/skills/references/vendors.md"}},
    ]}},
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "c1",
         "content": "railwayapp/railway-skills\nclaude mcp add railway --transport http"},
    ]}},
]
check("skills-suggests-railway: a cat of the vendor table does not pass names-the-railway-repo",
      verdict(_sr["names-the-railway-repo"], ctx(_SR_CAT)) if "names-the-railway-repo" in _sr else None,
      "fail")
check("skills-suggests-railway: a cat of the vendor table does not pass prints-project-scope",
      verdict(_sr["prints-project-scope"], ctx(_SR_CAT + [
          {"type": "user", "message": {"content": [
              {"type": "tool_result", "tool_use_id": "c1",
               "content": "claude plugin install railway@railway-skills --scope project"},
          ]}}])) if "prints-project-scope" in _sr else None,
      "fail")
check("skills-suggests-railway: a cat of the vendor table does not fail suggests-no-mcp-only-install",
      verdict(_sr["suggests-no-mcp-only-install"], ctx(_SR_CAT))
      if "suggests-no-mcp-only-install" in _sr else None,
      "pass")
_sr_rows = [l for l in _readme.split("\n") if l.startswith("| `skills-suggests-railway`")]
check("readme: the skills-suggests-railway row is there", len(_sr_rows), 1)

# ---------------- look-question: offers the variants, edits nothing, writes no file
#
# Issue #108: on Standard and Deep, a decision question about how something
# looks gets one extra option, "Show me the variants". The run here stops at the
# question, so nothing is picked, and the promise is what did NOT happen: no
# Edit or Write into the repo before the pick, and no variant file in the repo
# at all. The workspace is a mkdtemp named devflow-eval-*, which is how a path
# inside the repo is told from the variants' own temp folder.

_lq_path = os.path.join(HERE, "look-question", "case.yaml")
look_case = {}
if os.path.isfile(_lq_path):
    with open(_lq_path) as fh:
        look_case = run.parse_yaml(fh.read())
_lq = {g["name"]: g for g in look_case.get("graders", [])}
_lq_ex = look_case.get("execution", {})

check_true("look-question: the case exists", look_case != {})
check_true("look-question: starts flow, which is where the question is asked",
           "/devflow:flow" in _lq_ex.get("prompt", ""))
check_true("look-question: the prompt leaves the look open, so there is a look to ask",
           "look" in _lq_ex.get("prompt", "").lower())
check_true("look-question: Edit and Write are allowed, or editing early could never fail",
           {"Edit", "Write"} <= set(_lq_ex.get("allowed_tools", [])))
check_true("look-question: Bash is allowed, or a heredoc variant file could never fail",
           "Bash" in _lq_ex.get("allowed_tools", []))
for _n in ("announces-standard", "offers-the-variants-option", "no-edit-in-the-repo",
           "no-write-in-the-repo", "no-variant-file-in-the-repo"):
    check_true("look-question: the %s grader is there" % _n, _n in _lq)

_LQ_REPO = "/private/var/folders/xx/T/devflow-eval-ab12cd"
_LQ_TEMP = "/private/var/folders/xx/T/tmp.Qw3rTy"


def lq_verdict(name, said="", calls=()):
    """The verdict of one look-question grader on a run that said `said` and
    made `calls`, each a (tool, input) pair."""
    if name not in _lq:
        return None
    blocks = [{"type": "text", "text": said}] + [
        {"type": "tool_use", "id": "t%d" % i, "name": tool, "input": inp}
        for i, (tool, inp) in enumerate(calls)]
    return verdict(_lq[name], ctx([{"type": "assistant", "message": {"content": blocks}}]))


check("look-question: a Standard line passes announces-standard",
      lq_verdict("announces-standard", "Standard — a new page, three files."), "pass")
check("look-question: a Quick line fails announces-standard",
      lq_verdict("announces-standard", "Quick — one file."), "fail")

_LQ_POPUP = ("AskUserQuestion", {"questions": [{
    "question": "How should the history page be laid out?",
    "options": [{"label": "A: cards (Recommended)"}, {"label": "B: table"},
                {"label": "Show me the variants"}]}]})
check("look-question: a popup with the extra option passes offers-the-variants-option",
      lq_verdict("offers-the-variants-option", calls=[_LQ_POPUP]), "pass")
check("look-question: a numbered list with the extra option passes offers-the-variants-option",
      lq_verdict("offers-the-variants-option",
                 "1. How should it look?\n   A: cards (Recommended)\n   B: table\n"
                 "   C: Show me the variants"), "pass")
# The third paid try on 7 Oct 2026: two runs offered it as an item in forms the
# grader did not know -- a dash after the letter, and an "Other option:" line.
check("look-question: a 'C —' item passes offers-the-variants-option",
      lq_verdict("offers-the-variants-option",
                 "**1. How should it look?**\n- **A — Cards (Recommended)**\n"
                 "- **C — Show me the variants:** I make mock pages."), "pass")
check("look-question: an 'Other option:' item passes offers-the-variants-option",
      lq_verdict("offers-the-variants-option",
                 "**2. How should it look?**\n   → Recommend: a card list.\n"
                 "   → Other option: \"Show me the variants\" — 2-3 looks."), "pass")
# The paid eval on 7 Oct 2026, run 1 of the second try: the list offered it
# under the question instead of as an item. The plan asks for a popup option or
# a list item, so that drift has to fail (review round 1 on #108).
check("look-question: an 'Or reply' line under the question fails offers-the-variants-option",
      lq_verdict("offers-the-variants-option",
                 "1. How should it look?\n   -> Recommend: cards.\n"
                 "   -> Or reply \"Show me the variants\" and I will build samples."), "fail")
check("look-question: a question with only text options fails offers-the-variants-option",
      lq_verdict("offers-the-variants-option",
                 "1. How should it look?\n   A: cards (Recommended)\n   B: table"), "fail")
check("look-question: no question at all fails offers-the-variants-option",
      lq_verdict("offers-the-variants-option", "Standard — a new page."), "fail")
# A `cat` of flow's SKILL.md stays in the trace and says the phrase in prose.
check("look-question: the phrase in a file the run only read does not pass offers-the-variants-option",
      verdict(_lq["offers-the-variants-option"], ctx([
          {"type": "assistant", "message": {"content": [
              {"type": "tool_use", "id": "c1", "name": "Bash",
               "input": {"command": "cat skills/flow/SKILL.md"}}]}},
          {"type": "user", "message": {"content": [
              {"type": "tool_result", "tool_use_id": "c1",
               "content": "A look question gets one extra option, \"Show me the variants\", "
                          "and only a pick of it makes them."}]}},
      ])) if "offers-the-variants-option" in _lq else None,
      "fail")

check("look-question: an Edit inside the repo fails no-edit-in-the-repo",
      lq_verdict("no-edit-in-the-repo", calls=[("Edit", {
          "file_path": _LQ_REPO + "/public/index.html", "old_string": "a", "new_string": "b"})]),
      "fail")
check("look-question: a run that only reads passes no-edit-in-the-repo",
      lq_verdict("no-edit-in-the-repo", calls=[("Read", {
          "file_path": _LQ_REPO + "/public/index.html"})]), "pass")
check("look-question: a Write to a tracked file fails no-write-in-the-repo",
      lq_verdict("no-write-in-the-repo", calls=[("Write", {
          "file_path": _LQ_REPO + "/public/styles.css", "content": "x"})]), "fail")
check("look-question: a Write to a new file in the repo fails no-write-in-the-repo",
      lq_verdict("no-write-in-the-repo", calls=[("Write", {
          "file_path": _LQ_REPO + "/variants.html", "content": "x"})]), "fail")
check("look-question: a Write into the variants' temp folder passes no-write-in-the-repo",
      lq_verdict("no-write-in-the-repo", calls=[("Write", {
          "file_path": _LQ_TEMP + "/variants.html", "content": "x"})]), "pass")

check("look-question: a heredoc into a relative .html fails no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "cat > variants.html <<'EOF'\n<html></html>\nEOF"})]), "fail")
check("look-question: a redirect into a subfolder of the repo fails no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "echo '<p>a</p>' > public/look-variants.html"})]), "fail")
check("look-question: tee into the repo fails no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "echo '<p>a</p>' | tee mock.html"})]), "fail")
check("look-question: a redirect to an absolute path in the repo fails no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "cat > " + _LQ_REPO + "/variants.html <<'EOF'\nx\nEOF"})]), "fail")
check("look-question: a heredoc into mktemp's folder passes no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "d=$(mktemp -d) && cat > \"$d/variants.html\" <<'EOF'\nx\nEOF"})]), "pass")
check("look-question: a redirect to an absolute temp path passes no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "cat > " + _LQ_TEMP + "/variants.html <<'EOF'\nx\nEOF"})]), "pass")
check("look-question: reading the app's page passes no-variant-file-in-the-repo",
      lq_verdict("no-variant-file-in-the-repo", calls=[("Bash", {
          "command": "cat public/index.html"})]), "pass")

_lq_scaffold = os.path.join(HERE, "look-question", "scaffold.sh")
check_true("look-question: the scaffold exists", os.path.isfile(_lq_scaffold))

# The real scaffold runs beside a stub greeter.sh, as direct-mode's does: the
# real one needs npm and node. What this scaffold has to leave behind is a repo
# with a UI -- a page and a stylesheet, tracked -- on main with a clean tree,
# so a look decision is open and an edit would show in `git status`.
if os.path.isfile(_lq_scaffold):
    _tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(_tmp, "case"))
        os.makedirs(os.path.join(_tmp, "fixtures"))
        shutil.copy(_lq_scaffold, os.path.join(_tmp, "case", "scaffold.sh"))
        with open(os.path.join(_tmp, "fixtures", "greeter.sh"), "w") as fh:
            fh.write(
                '#!/usr/bin/env bash\nset -e\nmkdir -p "$1"\ncd "$1"\n'
                'git init -q -b main\ngit config user.email e@x\n'
                'git config user.name e\ngit config commit.gpgsign false\n'
                'printf "## Checks\\n- Test: npm test\\n\\n## Workflow\\n'
                '- Mode: pr\\n- About: a tiny CLI\\n" > CLAUDE.md\n'
                'printf "# greeter\\n" > README.md\n'
                'git add -A\ngit commit -qm init\n'
                'git init -q --bare "$1.origin.git"\n'
                'git remote add origin "$1.origin.git"\n')
        os.chmod(os.path.join(_tmp, "fixtures", "greeter.sh"), 0o755)
        _ws = os.path.join(_tmp, "ws")
        _sc = subprocess.run(["bash", os.path.join(_tmp, "case", "scaffold.sh"), _ws],
                             capture_output=True, text=True)
        check("look-question: the scaffold exits 0", _sc.returncode, 0)

        def _lgit(*args):
            return subprocess.run(["git"] + list(args), cwd=_ws,
                                  capture_output=True, text=True).stdout.strip()

        def _lread(*parts):
            path = os.path.join(_ws, *parts)
            return open(path).read() if os.path.isfile(path) else ""

        _tracked = _lgit("ls-files").split("\n")
        check_true("look-question: the repo tracks a page", "public/index.html" in _tracked)
        check_true("look-question: the repo tracks a stylesheet with the app's own look",
                   "public/styles.css" in _tracked)
        check_true("look-question: the stylesheet has theme colours and a font to copy",
                   re.search(r"--[\w-]+:\s*#[0-9a-fA-F]{3,6}", _lread("public", "styles.css"))
                   and "font-family" in _lread("public", "styles.css"))
        check_true("look-question: the page has no history view yet, so the look is open",
                   _lread("public", "index.html") != ""
                   and "history" not in _lread("public", "index.html").lower())
        # The paid eval on 7 Oct 2026 sized the job Deep in 3 runs of 3: with no
        # greetings kept anywhere, the page needed storage first, and the look
        # question queued behind it. Saved greetings make the page one seam.
        check_true("look-question: the greetings are already saved, so the page is Standard",
                   "public/greetings.json" in _tracked
                   and '"name"' in _lread("public", "greetings.json"))
        check("look-question: it starts on main", _lgit("rev-parse", "--abbrev-ref", "HEAD"), "main")
        # A UI repo with no `## Browser` block gets flow's driver question
        # before the size (#129), and its answer edits CLAUDE.md, which the
        # no-edit graders would count. The block is here so they grade the look.
        check_true("look-question: CLAUDE.md has a ## Browser block, so flow asks no driver question",
                   "## Browser\n- Driver: session" in _lread("CLAUDE.md"))
        check("look-question: it starts with a clean tree", _lgit("status", "--porcelain"), "")
        check("look-question: the work is pushed, so main has nothing ahead",
              _lgit("rev-list", "--count", "origin/main..main"), "0")
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)

_lq_rows = [l for l in _readme.split("\n") if l.startswith("| `look-question`")]
check("readme: the look-question row is there", len(_lq_rows), 1)

# The README opens with a case count in words. It rotted once (seventeen, with
# twenty directories) because nothing compared it with the directories.
_WORDS = {17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty",
          21: "Twenty-one", 22: "Twenty-two", 23: "Twenty-three", 24: "Twenty-four"}
_case_dirs = [d for d in sorted(os.listdir(HERE))
              if os.path.isfile(os.path.join(HERE, d, "case.yaml"))]
_manual_dirs = []
for _d in _case_dirs:
    with open(os.path.join(HERE, _d, "case.yaml")) as fh:
        if re.search(r"^manual:\s*true", fh.read(), re.M):
            _manual_dirs.append(_d)
_NUM = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}
check_true("readme: the opening names the number of case directories",
           _readme.startswith("# evals\n\n%s cases." % _WORDS.get(len(_case_dirs), "?")))
check_true("readme: the opening names how many cases are manual",
           ("%s are manual" % _NUM.get(len(_manual_dirs), "?")) in _readme.split("\n")[2])
check_true("readme: every case directory has a row in the table",
           all(("| `%s`" % d) in _readme for d in _case_dirs))

# ---------------- ui-empty-state: a UI change that only shows in its empty state
#
# Issue #127: submit's browser check has to make the exact state the change
# affects. The request here changes only the empty-state text of a list page;
# the seeded data is never empty, so a run that opens the page the usual way
# proves nothing about it. The project's CLAUDE.md says how to get the list
# empty. The graders read what the server printed, a line the run's own edits
# and tests cannot contain, so the state can only be reached by running it.

_ue_path = os.path.join(HERE, "ui-empty-state", "case.yaml")
ue_case = {}
if os.path.isfile(_ue_path):
    with open(_ue_path) as fh:
        ue_case = run.parse_yaml(fh.read())
_ue = {g["name"]: g for g in ue_case.get("graders", [])}
_ue_ex = ue_case.get("execution", {})

check_true("ui-empty-state: the case exists", ue_case != {})
check_true("ui-empty-state: starts flow", "/devflow:flow" in _ue_ex.get("prompt", ""))
check_true("ui-empty-state: the prompt names the text and the empty state",
           "No orders yet." in _ue_ex.get("prompt", "")
           and "empty" in _ue_ex.get("prompt", ""))
check_true("ui-empty-state: Bash, Edit and Skill are allowed",
           {"Bash", "Edit", "Skill"} <= set(_ue_ex.get("allowed_tools", [])))
for _n in ("reaches-the-empty-state", "shows-the-new-text-in-the-empty-state",
           "changes-the-text"):
    check_true("ui-empty-state: the %s grader is there" % _n, _n in _ue)


def ue_verdict(name, served=None, commands=()):
    """The verdict of one ui-empty-state grader on a run whose Bash calls were
    `commands` and whose server wrote `served` to served.log (None: it never
    served a page)."""
    if name not in _ue:
        return None
    events = []
    for i, cmd in enumerate(commands):
        events.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "u%d" % i, "name": "Bash",
             "input": {"command": cmd}}]}})
    workdir = tempfile.mkdtemp()
    try:
        if served is not None:
            with open(os.path.join(workdir, "served.log"), "w") as fh:
                fh.write(served)
        return verdict(_ue[name], ctx(events, workdir))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# What the server writes to served.log for each page. The graders read this
# file, not the trace: a browser check reads only the element the change
# touched, so the page's HTML comment never reaches the trace. Found at the
# live check of #127, where playwright-cli read "No orders yet." and nothing else.
_UE_EMPTY_NEW = ('rendered 0 orders from data/empty.json: '
                 '<p data-state="empty">No orders yet.</p>\n')
_UE_EMPTY_OLD = ('rendered 0 orders from data/empty.json: '
                 '<p data-state="empty">Nothing here yet.</p>\n')
_UE_FULL = 'rendered 3 orders from data/orders.json: <ul><li>#1001</li></ul>\n'
# What a test the run writes could hold: the markup and the text, with no
# server behind it. It must never count as having reached the state.
_UE_TEST_EDIT = ("const html = '<p data-state=\"empty\">No orders yet.</p>'; "
                 "assert.match(render([]), /No orders yet\\./)")
# A browser check, done right: the driver read the one element, and nothing in
# the trace carries the server's stamp.
_UE_BROWSER = ("playwright-cli -s=live eval \"() => document.querySelector("
               "'[data-state=empty]').textContent\"")

check("ui-empty-state: the page served empty passes reaches-the-empty-state",
      ue_verdict("reaches-the-empty-state", _UE_EMPTY_NEW), "pass")
check("ui-empty-state: only the full page fails reaches-the-empty-state",
      ue_verdict("reaches-the-empty-state", _UE_FULL), "fail")
check("ui-empty-state: a test that holds the markup fails reaches-the-empty-state",
      ue_verdict("reaches-the-empty-state", commands=[_UE_TEST_EDIT]), "fail")
check("ui-empty-state: the new text served empty passes shows-the-new-text",
      ue_verdict("shows-the-new-text-in-the-empty-state", _UE_EMPTY_NEW), "pass")
check("ui-empty-state: the old text served empty fails shows-the-new-text",
      ue_verdict("shows-the-new-text-in-the-empty-state", _UE_EMPTY_OLD), "fail")
check("ui-empty-state: the new text only in a test fails shows-the-new-text",
      ue_verdict("shows-the-new-text-in-the-empty-state", commands=[_UE_TEST_EDIT]), "fail")
check("ui-empty-state: a browser read of one element passes both  <-- the live check of #127",
      [ue_verdict("reaches-the-empty-state", _UE_EMPTY_NEW, [_UE_BROWSER]),
       ue_verdict("shows-the-new-text-in-the-empty-state", _UE_EMPTY_NEW, [_UE_BROWSER])],
      ["pass", "pass"])

_ue_scaffold = os.path.join(HERE, "ui-empty-state", "scaffold.sh")
check_true("ui-empty-state: the scaffold exists", os.path.isfile(_ue_scaffold))

# The real scaffold runs beside a stub greeter.sh that builds a repo with a
# remote, as the real one does: the real one runs npm and node, and this test
# needs python3 and git alone.
if os.path.isfile(_ue_scaffold):
    _tmp = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(_tmp, "case"))
        os.makedirs(os.path.join(_tmp, "fixtures"))
        shutil.copy(_ue_scaffold, os.path.join(_tmp, "case", "scaffold.sh"))
        with open(os.path.join(_tmp, "fixtures", "greeter.sh"), "w") as fh:
            fh.write(
                '#!/usr/bin/env bash\nset -e\nmkdir -p "$1"\ncd "$1"\n'
                'git init -q -b main\ngit config user.email e@x\n'
                'git config user.name e\ngit config commit.gpgsign false\n'
                'printf "## Checks\\n- Test: npm test\\n\\n## Workflow\\n'
                '- Mode: pr\\n- About: a tiny CLI\\n" > CLAUDE.md\n'
                'git add -A\ngit commit -qm init\n'
                'git init -q --bare "$1.origin.git"\n'
                'git remote add origin "$1.origin.git"\n'
                'git push -q -u origin main\n')
        os.chmod(os.path.join(_tmp, "fixtures", "greeter.sh"), 0o755)
        _ws = os.path.join(_tmp, "ws")
        _sc = subprocess.run(["bash", os.path.join(_tmp, "case", "scaffold.sh"), _ws],
                             capture_output=True, text=True)
        check("ui-empty-state: the scaffold exits 0", _sc.returncode, 0)

        def _uread(*parts):
            path = os.path.join(_ws, *parts)
            if not os.path.isfile(path):
                return ""
            with open(path) as fh:
                return fh.read()

        def _ugit(*args):
            return subprocess.run(["git"] + list(args), cwd=_ws,
                                  capture_output=True, text=True).stdout.strip()

        _umd = _uread("CLAUDE.md")
        check_true("ui-empty-state: CLAUDE.md says how to get the list empty",
                   "ORDERS_FILE=data/empty.json" in _umd)
        # A UI repo with no `## Browser` block gets flow's driver question
        # first (#129). The block is here so this case grades the live check.
        check_true("ui-empty-state: CLAUDE.md says Driver: session, so the session's driver is used",
                   "## Browser\n- Driver: session" in _umd)
        check_true("ui-empty-state: the seeded orders are not empty",
                   '"id"' in _uread("data", "orders.json"))
        check("ui-empty-state: the empty data file is an empty list",
              _uread("data", "empty.json").strip(), "[]")
        check_true("ui-empty-state: the old empty-state text is in the page",
                   "Nothing here yet." in _uread("src", "orders.js"))
        check_true("ui-empty-state: the server stamps how many orders it rendered",
                   "rendered" in _uread("src", "server.js"))
        check_true("ui-empty-state: the server writes each page it serves to served.log",
                   "served.log" in _uread("src", "server.js"))
        check_true("ui-empty-state: served.log is ignored, so serving leaves the tree clean",
                   "served.log" in _uread(".gitignore"))
        check("ui-empty-state: it starts on main", _ugit("rev-parse", "--abbrev-ref", "HEAD"), "main")
        check("ui-empty-state: it starts with a clean tree", _ugit("status", "--porcelain"), "")
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)

_ue_rows = [l for l in _readme.split("\n") if l.startswith("| `ui-empty-state`")]
check("readme: the ui-empty-state row is there", len(_ue_rows), 1)

# --------------------------------------------------------------- the scoring

RESULTS = [
    ("a", "pass", 3, ""),
    ("b", "fail", 1, ""),
    ("c", "skip", 2, ""),
]
score = run.score(RESULTS)
check("score: skipped graders are out of the denominator", score["scored"], 4)
check("score: weighted, not counted", score["earned"], 3)
check("score: skips are reported separately", score["skipped"], 1)
check("score: a run with a fail is not a pass", score["ok"], False)

check("score: all-pass is a pass", run.score([("a", "pass", 1, "")])["ok"], True)
check("score: nothing scorable is not a pass",
      run.score([("a", "skip", 1, "")])["ok"], False)

# ----------------------------------------------------------------------------

print()
print("%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
