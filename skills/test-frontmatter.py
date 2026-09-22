#!/usr/bin/env python3
"""Contract tests for the skills' and agents' YAML frontmatter.

    python3 skills/test-frontmatter.py

A skill's `description` is the only thing deciding whether it fires at all, and
it reaches the model through a YAML parser. So a value that parses differently
from how it reads on disk is invisible twice over: invisible in review, because
the file looks right, and invisible at runtime, because a truncated description
is still a perfectly valid description.

That is not hypothetical. `flow`'s description contained `... issue number like
#123 ...`, and in a plain YAML scalar a `#` preceded by whitespace opens a
comment. 604 characters on disk, 544 delivered. The dropped tail ended with
"This is the entry point, start here." -- the sentence most likely to make the
skill trigger, silently discarded since the day it was written. `flow` then sat
there not triggering, and the missing sentence was never a suspect.

`argument-hint` on the very next line was already quoted for exactly this
reason. One line up, it was missed.

The rule enforced here: **no YAML metacharacter may sit unquoted in a
frontmatter value.** That is a lint, not a reimplementation of YAML, and
deliberately so -- a half-correct parser in a test is worse than no test,
because it reads as coverage. Where PyYAML happens to be importable the suite
also round-trips every file through a real parser and asserts the lint agreed;
where it is not, the lint still stands on its own.
"""

import os
import re
import subprocess
import sys

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(os.path.dirname(SKILLS_DIR), "agents")

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


def frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else None


def fields(fm):
    """Top-level `key: value` pairs. These files use no nesting."""
    out = []
    for line in fm.split("\n"):
        if not line.strip() or line.lstrip().startswith("#") or line[0] in " \t":
            continue
        key, sep, value = line.partition(":")
        if sep:
            out.append((key.strip(), value.strip()))
    return out


# YAML indicators that change a value's meaning when they open a plain scalar.
INDICATORS = "[]{}>|*&!%@`"


def hazard(value):
    """Why a spec YAML parser would read this value differently, or None."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return None                       # quoted: it says what it means
    if value[:1] in ("\"", "'"):
        return "opens a quote it never closes"
    if value[:1] and value[0] in INDICATORS:
        return f"starts with {value[0]!r}, a YAML indicator, so it is not read as text"
    m = re.search(r"\s#", value)
    if m:
        return (f"unquoted ' #' at column {m.start()} opens a comment - "
                f"the last {len(value) - m.start()} characters are dropped")
    if ": " in value:
        return "unquoted ': ' - YAML reads this as a nested mapping"
    if value.endswith(":"):
        return "unquoted trailing ':' - YAML reads this as a key"
    return None


def literal(value):
    """The text a parser yields for a value. No escapes are used in these files."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


# --------------------------------------------------------------- the skills

skills = sorted(
    d for d in os.listdir(SKILLS_DIR)
    if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md"))
)

# Without this the whole suite passes by finding nothing, which reads as
# coverage and is not.
check("found the skills to check", len(skills) >= 4, f"found {skills!r}")

parsed = {}

for slug in skills:
    path = os.path.join(SKILLS_DIR, slug, "SKILL.md")
    with open(path, encoding="utf-8") as fh:
        fm = frontmatter(fh.read())

    check(f"{slug}: has a frontmatter block", fm is not None)
    if fm is None:
        continue

    pairs = fields(fm)
    parsed[slug] = (fm, dict(pairs))
    values = dict(pairs)

    check(f"{slug}: name matches its directory",
          values.get("name") == slug,
          f"name={values.get('name')!r}, directory={slug!r}")

    check(f"{slug}: has a description", bool(literal(values.get("description", ""))))

    for key, value in pairs:
        why = hazard(value)
        check(f"{slug}: {key} survives YAML intact", why is None, why)

# --------------------------------------------------------------- the agents
#
# Same contract, same parser, one directory up. An agent's description decides
# whether it is the right agent to hand a job to, so a truncated one is the same
# silent failure as a truncated skill description.
#
# Agents also carry the routing. `model` and `effort` are omittable, and both
# default to inheriting the session -- so an agent that declares neither is not
# broken, it is quietly whatever the human last typed at `/model`. A review run
# on a weaker model than intended still prints a review, and still says nothing
# went wrong. That is the same silent failure as a truncated description, which
# is why the two are checked in the same place.
#
# `inherit` is a real value and deliberately not accepted here: it is spelled
# the same as forgetting.

AGENT_MODELS = {"opus", "sonnet", "haiku", "fable"}
AGENT_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def pins_a_model(value):
    """Whether this value names one model. An alias or a full id, not `inherit`."""
    return value in AGENT_MODELS or value.startswith("claude-")


agents = sorted(
    f for f in os.listdir(AGENTS_DIR) if f.endswith(".md")
) if os.path.isdir(AGENTS_DIR) else []

check("found the agents to check", len(agents) >= 1, f"found {agents!r}")

for filename in agents:
    slug = filename[:-len(".md")]
    label = f"agents/{slug}"
    path = os.path.join(AGENTS_DIR, filename)
    with open(path, encoding="utf-8") as fh:
        fm = frontmatter(fh.read())

    check(f"{label}: has a frontmatter block", fm is not None)
    if fm is None:
        continue

    pairs = fields(fm)
    parsed[label] = (fm, dict(pairs))
    values = dict(pairs)

    check(f"{label}: name matches its filename",
          values.get("name") == slug,
          f"name={values.get('name')!r}, file={filename!r}")

    check(f"{label}: has a description", bool(literal(values.get("description", ""))))

    for key, value in pairs:
        why = hazard(value)
        check(f"{label}: {key} survives YAML intact", why is None, why)

    model = literal(values.get("model", ""))
    check(f"{label}: pins a model", pins_a_model(model),
          f"model={model!r}, expected one of {sorted(AGENT_MODELS)} or a "
          f"claude-* id. Unset or 'inherit' means the review runs on whatever "
          f"the session happened to be set to")

    effort = literal(values.get("effort", ""))
    check(f"{label}: pins an effort level", effort in AGENT_EFFORTS,
          f"effort={effort!r}, expected one of {sorted(AGENT_EFFORTS)}")

# ------------------------- the builder does NOT pin a worktree in frontmatter
#
# `flow` starts several builders at once, one per chain, each in its own
# worktree -- but it asks for that on the Agent call, per spawn, not here.
# The reason is the sequential path: when the harness has no worktree
# isolation, or `flow` has just written `worktree.baseRef` and it is not in
# force yet, `flow` spawns the same builder WITHOUT a worktree so it commits
# on the feature branch. A frontmatter `isolation: worktree` cannot be turned
# off per spawn, so with it pinned that path would still cut worktrees, from
# the default branch, and nothing would reach the feature branch. The review
# of 22 Sep 2026 found exactly that. So the frontmatter must leave it unset,
# and `flow`'s spawn step must be the one place that says `isolation`.

builder_values = parsed.get("agents/builder", (None, {}))[1]

check("agents/builder: has a frontmatter block to check",
      bool(builder_values),
      "agents/builder.md was never parsed above")

check("agents/builder: leaves isolation to flow's Agent call",
      "isolation" not in builder_values,
      f"isolation={builder_values.get('isolation')!r}, expected unset. "
      f"Pinned here it cannot be switched off for the sequential path, "
      f"which then cuts worktrees from the default branch")

with open(os.path.join(SKILLS_DIR, "flow", "SKILL.md"), encoding="utf-8") as fh:
    flow_body = fh.read()

check("flow: asks for the worktree on the Agent call",
      'isolation:\n   "worktree"' in flow_body or 'isolation: "worktree"' in flow_body,
      "skills/flow/SKILL.md never says to pass isolation: \"worktree\" when spawning")


# ------------------------------- and the directory that isolation creates
#
# The harness puts each builder's checkout under `.claude/worktrees/`. That is a
# checkout of this same repo, so leaving it untracked turns one parallel Deep run
# into hundreds of files in `git status` -- and `submit`, which stages what is
# there, would commit a checkout into the repo it was cut from. Anthropic's
# worktrees page says to ignore it. The line is checked here, next to the
# `isolation` setting that is the reason the directory exists at all: the two go
# in together or neither is safe.

REPO_ROOT = os.path.dirname(SKILLS_DIR)
WORKTREE_DIR = ".claude/worktrees/"

try:
    with open(os.path.join(REPO_ROOT, ".gitignore"), encoding="utf-8") as fh:
        gitignore_lines = [line.strip() for line in fh]
except FileNotFoundError:
    gitignore_lines = []

check("gitignore: lists the builders' worktree directory",
      WORKTREE_DIR in gitignore_lines,
      f"no {WORKTREE_DIR!r} line in .gitignore. Every builder's checkout lands "
      f"there, and an unignored one is untracked files the next commit sweeps up")


def in_a_git_work_tree():
    """Whether git is here and this copy is a checkout. The plugin cache is not."""
    try:
        done = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                              cwd=REPO_ROOT, capture_output=True, text=True)
    except OSError:
        return False
    return done.returncode == 0 and done.stdout.strip() == "true"


# Same shape as the PyYAML cross-check below: where git is available, ask git
# itself rather than trusting a string match on the file. Where it is not -- the
# installed plugin is a plain copied directory -- the text check above still
# stands on its own.
if in_a_git_work_tree():
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", WORKTREE_DIR + "chain-a"],
        cwd=REPO_ROOT, capture_output=True, text=True)
    check("gitignore: git itself ignores a builder's worktree",
          ignored.returncode == 0,
          f"git check-ignore exited {ignored.returncode} for "
          f"{WORKTREE_DIR + 'chain-a'!r}; 0 means ignored")
else:
    print("\nnote: not a git work tree, so the git check-ignore cross-check was\n"
          "      skipped. The .gitignore line is still checked above.\n")


# ------------------- and the base the harness cuts those worktrees from
#
# A subagent's worktree branches from the repository's *default* branch, not
# from the branch the session is standing on, unless `worktree.baseRef` is set
# to "head". Anthropic's worktrees page says so outright. Nothing announces the
# difference: every chain still builds, every test still passes, and every one
# of them is missing the stacked base branch and every chain merged before it --
# the damage shows up at the merge, as a diff nobody can explain.
#
# So `flow` writes the setting itself, and then proves it took, because the
# setting may only be read when a session starts. Four things are load-bearing
# and a prompt is the only place any of them lives: the key's exact spelling,
# the file it is written to, the refusal to write the committed one, and the
# command that checks the result. They are pinned as text here for the same
# reason the `.gitignore` line above is.

FLOW_PATH = os.path.join(SKILLS_DIR, "flow", "SKILL.md")
with open(FLOW_PATH, encoding="utf-8") as fh:
    flow_text = fh.read()

SETTINGS_LINE = (
    "settings: wrote worktree.baseRef = head to .claude/settings.local.json "
    "\u2014 chain worktrees branch from here, and so will your own --worktree sessions"
)

STOP_LINE = (
    "chain <letter> branched from the default branch \u2014 the setting did not "
    "take; restart the session and run flow again to resume"
)

check("flow: prints the worktree.baseRef line word for word",
      SETTINGS_LINE in flow_text,
      f"no line {SETTINGS_LINE!r} in {FLOW_PATH}. The human reads that line and "
      f"nothing else says their own --worktree sessions changed too")

check("flow: refuses to write the committed settings file",
      re.search(r"[Nn]ever write[^\n]*\.claude/settings\.json", flow_text)
      is not None,
      "no 'never write .claude/settings.json' rule in flow. That file is "
      "committed, and baseRef is a preference about one machine")

check("flow: checks the chain branch descends from this one",
      "git merge-base --is-ancestor" in flow_text,
      "flow never runs 'git merge-base --is-ancestor'. Writing the setting is "
      "not proof it took -- it may only be read at session start")

check("flow: says what to do when the setting did not take",
      STOP_LINE in flow_text,
      f"no line {STOP_LINE!r} in {FLOW_PATH}. A chain off the wrong base must "
      f"stop the loop, not get merged")


# A setting written a moment ago is not in force: settings are read when a
# session starts, and this session started before `flow` wrote the file. So the
# very run that writes `worktree.baseRef` is the one run that must not spawn
# chains -- every worktree it cut would come off the default branch, the
# ancestor check would catch it, and a whole job's work would have to be rebuilt
# after a restart. That run takes the sequential path instead and says so in one
# line. The line and the rule are pinned here for the same reason the four above
# are: a prompt is the only place either of them lives.

WROTE_NOW_LINE = (
    "chains next session: worktree.baseRef was just written"
)

check("flow: names the run that just wrote the setting",
      WROTE_NOW_LINE in flow_text,
      f"no line {WROTE_NOW_LINE!r} in {FLOW_PATH}. The run that writes the "
      f"setting cannot use it, and has to say which run can")

check("flow: that run does not spawn chains",
      re.search(r"[Dd]o not spawn chains", flow_text) is not None,
      "flow never says not to spawn chains on the run that wrote the setting. "
      "Writing it and spawning anyway cuts every worktree from the wrong base")


# ------------------------ the untracked plan file is not a dirty tree
#
# In file mode the plan lives at `.devflow/plans/<name>.md` and is untracked
# until `submit` commits it, so `git status --short` prints a `??` line for it
# on every resume. Step 0b reads that line to decide whether a piece was left
# half-built, and a half-built piece sends one chain down the sequential path
# with `dirty` handed to the builder. Read the plan file as dirt and every
# file-mode resume serialises a chain and tells `build` to preserve work that
# does not exist. Found by the final look on 22 Sep 2026.

check("flow: discounts the untracked plan file when reading the tree as dirty",
      "?? .devflow/plans/" in flow_text,
      f"{FLOW_PATH} never says a `?? .devflow/plans/` line is not dirt")


# ------------------------------- step 1 takes a backlog file as the request
#
# `flow` parks the features it does not build to `.devflow/backlog/<name>.md`
# (or a GitHub issue). A later run given that path has to read it as the
# request rather than as a literal string to size, and it has to delete the
# file so the deletion ships in that run's own PR -- otherwise the same
# backlog entry gets read, and parked, forever. The exact printed line is
# pinned here so it cannot silently drift from what a resumed run expects to
# see, the same reason the settings and stop lines above are pinned.

BACKLOG_TAKEN_LINE = (
    "backlog: took .devflow/backlog/<name>.md — the file is deleted "
    "in this branch"
)

check("flow: step 1 reads a backlog path as the request and deletes it",
      BACKLOG_TAKEN_LINE in flow_text,
      f"no line {BACKLOG_TAKEN_LINE!r} in {FLOW_PATH}. A request under "
      f".devflow/backlog/ has to be read as the request, and the file "
      f"deleted, with this exact line printed")

check("flow: step 0b discounts the untracked backlog directory too",
      "?? .devflow/backlog/" in flow_text,
      f"{FLOW_PATH} never says a `?? .devflow/backlog/` line is not dirt")

flow_values = parsed.get("flow", (None, {}))[1]

check("flow: description says it accepts a backlog file path",
      "backlog" in flow_values.get("description", "").lower(),
      "flow's description never mentions accepting a backlog file path")

check("flow: argument-hint mentions the backlog path",
      "backlog" in flow_values.get("argument-hint", "").lower(),
      "flow's argument-hint never mentions a backlog file path")

FLOW_BACKLOG_TOOLS = [
    "Bash(gh issue list:*)",
    "Bash(gh issue create:*)",
    "Bash(gh label create:*)",
    "Bash(rm .devflow/backlog/*)",
]

for tool in FLOW_BACKLOG_TOOLS:
    check(f"flow: allowed-tools includes {tool}",
          tool in flow_values.get("allowed-tools", ""),
          f"flow's allowed-tools never lists {tool!r}")


# ------------------------------------ ship refuses and protects stacked PRs
#
# On 22 Sep 2026 `gh pr merge 23 --rebase --delete-branch` closed #24, which
# was stacked on #23's branch. GitHub did not retarget it, and once the base
# branch was gone it refused both `gh pr edit --base` and `gh pr reopen`; the
# only way out was a fresh PR. Two rules follow, and both live only in the
# prompt, so they are pinned here: a PR whose base is not the default branch
# is not merged from `ship`, and a PR that other open PRs are based on is
# merged without deleting its branch until those PRs point at the default
# branch.

SHIP_PATH = os.path.join(SKILLS_DIR, "ship", "SKILL.md")
with open(SHIP_PATH, encoding="utf-8") as fh:
    ship_text = fh.read()

check("ship: reads the PR's base before merging",
      "baseRefName" in ship_text,
      f"{SHIP_PATH} never asks for baseRefName, so a stacked PR merges into "
      f"its base branch instead of the default one")

check("ship: stops on a PR whose base is not the default branch",
      re.search(r"stacked", ship_text) is not None
      and re.search(r"base PR\b.*first", ship_text) is not None,
      f"{SHIP_PATH} never says a stacked PR's base PR must ship first")

check("ship: finds the PRs stacked on the one it is merging",
      "gh pr list --base" in ship_text,
      f"{SHIP_PATH} never lists the open PRs based on this PR's head branch")

check("ship: retargets stacked PRs before deleting the branch",
      "gh pr edit" in ship_text and "--base" in ship_text,
      f"{SHIP_PATH} never retargets a stacked PR with gh pr edit --base, so "
      f"deleting the branch closes it for good")


# ------------------------------ the final look may fix one small thing
#
# `submit` step 7 gives the fixes made after the last review one short look,
# and until 22 Sep 2026 anything that look found went straight under Known
# issues, so the fix-then-look loop would end. It found something on almost
# every PR -- #23, #25 and #26 each shipped with a one-line Known issue that
# a minute would have fixed -- and each one became a follow-up for the human
# to remember. So the look now gets one bounded fix: small, and in a file the
# branch already changed. Both conditions, the "no further look" that keeps
# the loop bounded, and the Evidence line that says the last edit went unread
# live only in the prompt, so they are pinned here like the rules above.

SUBMIT_PATH = os.path.join(SKILLS_DIR, "submit", "SKILL.md")
with open(SUBMIT_PATH, encoding="utf-8") as fh:
    submit_text = fh.read()

check("submit: the final look's fix must be small",
      "a few lines" in submit_text,
      f"{SUBMIT_PATH} never bounds the final look's fix by size ('a few lines')")

check("submit: the final look's fix must be in a file already on the branch",
      "file already changed on this branch" in submit_text,
      f"{SUBMIT_PATH} never says the fix has to land in a file already changed "
      f"on this branch")

check("submit: after the one fix there is no further look",
      re.search(r"[Nn]o further look", submit_text) is not None,
      f"{SUBMIT_PATH} never says 'no further look' -- without it the loop "
      f"the bounded fix was meant to end is open again")

check("submit: names the fix under Evidence as unread by an agent",
      "unread by an agent" in submit_text
      and "**Evidence**" in submit_text,
      f"{SUBMIT_PATH} never tells the PR reader that the final look's fix went "
      f"unread by an agent")

DOCS_SUBMIT_PATH = os.path.join(REPO_ROOT, "docs", "submit.md")
with open(DOCS_SUBMIT_PATH, encoding="utf-8") as fh:
    docs_submit_text = fh.read()

check("docs/submit: says why the look gets one fix, citing #23, #25 and #26",
      all(f"#{n}" in docs_submit_text for n in (23, 25, 26)),
      f"{DOCS_SUBMIT_PATH} does not cite the three PRs that shipped a "
      f"one-line Known issue the look could have fixed")


# ------------------------------------- ship's report names the retargeted PRs
#
# `ship` step 6 promises "step 7 names the PRs you retargeted", and step 7's
# report template did not list them -- the final look on #26 found it, and it
# went under Known issues because that was the rule. The template line is
# pinned here so the promise and the report cannot drift apart again.

check("ship: the report names the PRs it retargeted",
      "Retargeted:" in ship_text,
      f"{SHIP_PATH} step 7 has no 'Retargeted:' line, so step 6's promise "
      f"that step 7 names them is not kept")


# ------------------------------------------- cross-check against a real parser

try:
    import yaml
except ImportError:
    yaml = None

if yaml is None:
    print("\nnote: PyYAML not importable, so the parser cross-check was skipped.\n"
          "      The lint above ran regardless and is the load-bearing part.\n")
else:
    # A bool is the one value whose parsed form is spelled differently from its
    # source and still round-trips: `true` parses to Python True, whose str() is
    # `True`. Comparing the two as text reported every `disable-model-invocation`
    # as a mismatch -- a false positive in the one test whose whole job is
    # telling a real mismatch from a file that merely looks right.
    YAML_TRUE = ("true", "yes", "on", "1")
    YAML_FALSE = ("false", "no", "off", "0")

    def round_trips(loaded_value, on_disk):
        if isinstance(loaded_value, bool):
            spellings = YAML_TRUE if loaded_value else YAML_FALSE
            return on_disk.strip().lower() in spellings
        return str(loaded_value) == on_disk

    for slug, (fm, values) in parsed.items():
        loaded = yaml.safe_load(fm) or {}
        for key, value in values.items():
            check(f"{slug}: {key} round-trips through PyYAML",
                  round_trips(loaded.get(key, ""), literal(value)),
                  f"on disk {literal(value)[-60:]!r}\n"
                  f"     parsed  {str(loaded.get(key, ''))[-60:]!r}")

    # Same rule as the lint self-test below. A comparison that cannot fail is
    # not a check, and the bool case above only widened what counts as equal.
    check("round-trip self-test: True accepts 'true'", round_trips(True, "true"))
    check("round-trip self-test: True rejects 'false'",
          not round_trips(True, "false"))
    check("round-trip self-test: text is still compared exactly",
          round_trips("start here.", "start here.")
          and not round_trips("start here.", "start here"))

# ------------------------------- the lint must be able to fail, or it is noise

SAMPLES = [
    ("a comment that truncates", "Use it, issue #123, start here.", True),
    ("a bare YAML indicator", "[--quick|--deep] what you want", True),
    ("a colon that nests", "Sizes it: Quick, Standard or Deep", True),
    ("an unterminated quote", '"never closed', True),
    ("a trailing colon", "routes it to build:", True),
    ("the same text, quoted", '"Use it, issue #123, start here."', False),
    ("plain text with nothing special", "Use when the code changes", False),
    ("a tool list with colons but no spaces", "Bash(git status:*), Bash(git log:*)", False),
]

for name, value, should_object in SAMPLES:
    why = hazard(value)
    if should_object:
        check(f"lint self-test: rejects {name}", why is not None,
              "the lint raised no objection")
    else:
        check(f"lint self-test: accepts {name}", why is None, why)

# --------------------------------------------------------------------- report

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
