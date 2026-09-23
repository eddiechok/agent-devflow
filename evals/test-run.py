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
