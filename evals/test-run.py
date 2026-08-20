#!/usr/bin/env python3
"""Contract tests for evals/run.py.

Nothing here calls Claude. These test the two parts of the runner that can be
wrong silently: the YAML subset parser, and the graders. Both fail in the
direction this repo cares about — a grader that scores a run nobody made, and a
parser that reads a case file as something other than what it says.

Run: python3 evals/test-run.py
"""

import json
import os
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

# Spot-check one value the naive parser would get wrong.
with open(os.path.join(HERE, "full-loop", "case.yaml")) as fh:
    full_loop = run.parse_yaml(fh.read())
merge_graders = [g for g in full_loop["graders"] if "merge" in str(g.get("input_match", ""))]
check(
    "parser: full-loop's merge graders survive with their trailing space",
    sorted(g["input_match"] for g in merge_graders),
    ["gh pr merge", "git merge "],
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
