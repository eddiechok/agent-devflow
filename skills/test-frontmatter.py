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

import json
import os
import re
import subprocess
import sys
import tempfile

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


def flat(text):
    """One line, single-spaced. These files wrap their prose at about 95
    columns, so a pinned phrase long enough to be worth pinning is a phrase
    long enough to wrap. Pinning the wrap as well would fail the next time a
    word ahead of it changed, which is a test that punishes editing."""
    return " ".join(text.split())


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
    "\u2713 **settings** wrote worktree.baseRef = head to .claude/settings.local.json "
    "chain worktrees branch from here, and so will your own --worktree sessions"
)

STOP_LINE = (
    "\u2717 **chains** chain <letter> branched from the default branch the "
    "setting did not take; restart the session and run flow again to resume"
)

# Both lines are pinned against `flat(flow_text)`, not `flow_text` -- each now
# prints as two physical lines, the shaped one and a detail line straight
# after it, to keep the shaped line itself at or under 80 visible columns.
# `flat` is what already lets every other multi-line pin in this file survive
# a rewrap; these are no different.

check("flow: prints the worktree.baseRef line word for word",
      SETTINGS_LINE in flat(flow_text),
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
      STOP_LINE in flat(flow_text),
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
    "– **chains** worktree.baseRef was just written — this run does "
    "not spawn chains"
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
    "✓ **backlog** took .devflow/backlog/<name>.md — the file is deleted "
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


# ------------------------------- step 1b: one feature per run, not three in a PR
#
# A request that names three features either ends as one PR carrying all
# three, or a plan that mixes them. Step 1b asks, before the size line,
# because the size depends on which feature is kept -- and the round is
# free, so it must not count against step 4's question budget. The
# `features:` line is pinned so flow never opens the split with a bare
# question, the same reason the size line always comes first.

check("flow: has a step 1b for splitting a multi-feature request",
      "## Step 1b" in flow_text,
      f"{FLOW_PATH} has no '## Step 1b' section")

check("flow: step 1b leaves a request that names its own pieces as one feature",
      "each as its own piece" in flow_text.lower() and "one feature with pieces" in flow_text,
      "a request that already says how to build it must not be split")

check("flow: prints the features-found line before asking",
      "✓ **features** N found — one per run" in flow_text,
      f"{FLOW_PATH} never prints '✓ **features** N found — one per run'")

check("flow: asks whether to park the rest, with a recommendation",
      "park the rest" in flow_text and "Recommend: yes" in flow_text,
      f"{FLOW_PATH} step 1b never asks to park the rest with a recommendation")

check("flow: asks which feature to keep first, with a recommendation",
      "Which first" in flow_text,
      f"{FLOW_PATH} step 1b never asks which feature to build first")

check("flow: accepts 'yes to all' on the split round",
      flow_text.count('"yes to all"') >= 2,
      f"{FLOW_PATH} step 1b never accepts \"yes to all\" like step 4's round does")

check("flow: says the split round does not count against step 4's rounds",
      re.search(r"does not count against step 4", flow_text) is not None,
      f"{FLOW_PATH} never says the step 1b round is free")

check("flow: says --quick/--deep size only the kept feature",
      re.search(r"size the kept feature", flow_text) is not None,
      f"{FLOW_PATH} never says --quick/--deep size only the kept feature")

check("flow: step 2 sizes the kept feature alone",
      re.search(r"## Step 2.*?sizes? .* the kept feature alone",
                 flow_text, re.S) is not None,
      f"{FLOW_PATH} step 2 never says it sizes the kept feature alone")

check("flow: the Rules list carries the one-feature-per-run rule",
      re.search(r"## Rules.*one feature per run", flow_text, re.S) is not None,
      f"{FLOW_PATH}'s Rules list never mentions one feature per run")


# --------------------------- step 1b parks the rest, to GitHub or to a file
#
# The label create command, the issue create command, the file shape and the
# printed `parked:` line are exact commands and exact text a resumed run and
# a human both read literally, so they are pinned word for word -- the same
# reason the settings and stop lines earlier in this file are pinned.

BACKLOG_LABEL_CMD = (
    'gh label create devflow:backlog --description "A devflow parked feature" '
    "--color 5319E7"
)

check("flow: step 1b creates the devflow:backlog label before filing issues",
      BACKLOG_LABEL_CMD in flow_text,
      f"no line {BACKLOG_LABEL_CMD!r} in {FLOW_PATH}")

BACKLOG_ISSUE_CMD = (
    "gh api repos/{owner}/{repo}/issues -f title="
)

check("flow: step 1b files a devflow:backlog issue per parked feature",
      BACKLOG_ISSUE_CMD in flow_text
      and "-F body=@<body file> -f 'labels[]=devflow:backlog'" in flow_text,
      f"{FLOW_PATH} never runs 'gh api repos/{{owner}}/{{repo}}/issues "
      f"-f title=... -F body=@<body file> "
      f"-f 'labels[]=devflow:backlog'', the REST form")

check("flow: step 1b writes a backlog file with the parked-from line",
      ".devflow/backlog/<short-name>.md" in flow_text
      and "Parked from:" in flow_text,
      f"{FLOW_PATH} never writes .devflow/backlog/<short-name>.md with a "
      f"'Parked from:' line")

check("flow: step 1b prints the parked: line for the issue case",
      "✓ **parked** #46 add export, #47 fix login" in flow_text,
      f"{FLOW_PATH} never prints the exact '✓ **parked** #46 add export, "
      f"#47 fix login' example")

check("flow: step 1b prints the parked: line for the file case",
      "✓ **parked** .devflow/backlog/add-export.md, .devflow/backlog/fix-login.md"
      in flow_text,
      f"{FLOW_PATH} never prints the exact file-case 'parked' example")

BACKLOG_FALLBACK_LINE = (
    "✗ **parked** github asked, wrote .devflow/backlog/<name>.md — gh said "
    "<the error>"
)

check("flow: step 1b falls back to the file on a gh failure",
      BACKLOG_FALLBACK_LINE in flow_text,
      f"no line {BACKLOG_FALLBACK_LINE!r} in {FLOW_PATH}")

# --------------------------- step 1b offers a chip per parked feature, too
#
# In the desktop app a parked feature can be one click from its own flow run:
# `spawn_task` puts a chip in front of the human, and the chip starts a new
# session in a fresh worktree. That worktree is cut from commits, so it cannot
# see a backlog file this run has not committed yet -- a chip pointing at the
# path would start a run with no request. So the issue case hands over the
# number, and the file case hands over the feature's own text. Where the tool
# does not exist -- the CLI, the web -- nothing changes: parking is the record,
# and a chip is only ever a shortcut to it.

CHIP_ISSUE_PROMPT = "/devflow:flow #<n>"

check("flow: step 1b offers a chip per parked feature through spawn_task",
      "mcp__ccd_session__spawn_task" in flow_text,
      f"{FLOW_PATH} never names mcp__ccd_session__spawn_task")

check("flow: step 1b's chip for a parked issue runs flow on the number",
      CHIP_ISSUE_PROMPT in flow_text,
      f"no chip prompt {CHIP_ISSUE_PROMPT!r} in {FLOW_PATH}")

check("flow: step 1b's chip for a parked file carries the text, not the path",
      "never the backlog path" in flow_text,
      f"{FLOW_PATH} never says a file-case chip carries the feature's text "
      f"and never the backlog path")

CHIP_LINE = "✓ **chips** 2 offered — each starts its own flow run in a fresh worktree"

check("flow: step 1b prints the chips: line",
      CHIP_LINE in flow_text,
      f"no line {CHIP_LINE!r} in {FLOW_PATH}")

# A file-case chip hands the parked text to the next run as free text, which
# step 1 treats as the human's own words. Text that came from an issue or a
# backlog file was never that, so it gets no file-case chip.

check("flow: step 1b offers no file-case chip for text the human did not type",
      "offer no file-case chip" in flow_text,
      f"{FLOW_PATH} never refuses a file-case chip for text from an issue "
      f"or a backlog file")

# A chip clicked before the kept PR merges cannot see the backlog file, and
# the kept PR commits it to the default branch afterwards: an entry for a
# feature that already shipped. Until 23 Sep 2026 the chip run named it under
# Known issues, which `submit` rebuilds from review and could drop. Now the
# chip run's commit and PR body carry a `Backlog:` line whether the file was
# there or not, and step 1 looks for that line before it builds a backlog
# file. The line, both lookups and both printed lines are pinned: the writer
# and the reader live in two skills, and one word of drift breaks the match.

CHIP_FILE_LINE = (
    "Also parked as .devflow/backlog/<short-name>.md — delete it in this "
    "branch if it is there."
)

check("flow: a file-case chip ends with the Also parked as line",
      CHIP_FILE_LINE in flat(flow_text),
      f"no line {CHIP_FILE_LINE!r} in {FLOW_PATH}")

check("flow: a chip run no longer leans on Known issues for a missing file",
      "say so under Known issues" not in flat(flow_text),
      f"{FLOW_PATH} still has a chip run name a missing backlog file under "
      f"Known issues, which submit can drop")

BACKLOG_ABSENT_LINE = (
    "– **backlog** .devflow/backlog/<name>.md is not in this checkout the "
    "commit names it, so a later run skips it"
)

# Pinned against `flat(flow_text)`: the shaped line and its detail print as
# two physical lines, to keep the shaped line at or under 80 visible columns.

check("flow: a chip run says when its backlog file is not in its checkout",
      BACKLOG_ABSENT_LINE in flat(flow_text),
      f"no line {BACKLOG_ABSENT_LINE!r} in {FLOW_PATH}")

BACKLOG_BUILT_LOG = (
    'git log <default branch ref> --fixed-strings '
    '--grep="Backlog: .devflow/backlog/<name>.md" --format=%h -1'
)
BACKLOG_BUILT_PRS = (
    "gh api 'search/issues?q=repo:{owner}/{repo}+is:pr+is:merged+in:body"
    "+%22Backlog:+.devflow/backlog/<name>.md%22' "
    "--jq '.items[] | select(.body | contains(\"Backlog: .devflow/backlog/<name>.md\")) "
    "| .number'"
)

check("flow: step 1 asks the default branch's log before taking a backlog file",
      BACKLOG_BUILT_LOG in flow_text,
      f"no command {BACKLOG_BUILT_LOG!r} in {FLOW_PATH}")

# GitHub's phrase search is loose: on 23 Sep 2026 a quoted phrase from #34's
# body also matched four merged PRs that do not contain it. A loose hit here
# deletes a real backlog entry and builds nothing, so the --jq filter checks
# the exact line again, and the search only narrows what gets fetched.

check("flow: step 1 asks the merged PRs too, for a body-only Backlog line",
      BACKLOG_BUILT_PRS in flow_text,
      f"no command {BACKLOG_BUILT_PRS!r} in {FLOW_PATH}")

BACKLOG_BUILT_LINE = (
    "– **backlog** .devflow/backlog/<name>.md already built in <sha or #n> "
    "deleting it, nothing else to build"
)

# Two holes the first review found. The request step 1 hands on to `submit`
# has to keep the `Also parked as` line, or `submit` never writes the
# `Backlog:` line and the fix does nothing. And a hit is keyed on the path
# alone, so a later feature parked under a name an old `Backlog:` line
# already holds would read as built and be deleted -- step 1b has to refuse
# that name when it parks.

check("flow: step 1 keeps the Also parked line in the request for submit",
      "keep that line in the request" in flat(flow_text),
      f"{FLOW_PATH} never says the `Also parked as` line stays in the "
      f"request step 5 hands to submit")

check("flow: step 1b never parks under a name a Backlog: line already holds",
      "a name a `Backlog:` line already holds" in flat(flow_text),
      f"{FLOW_PATH} step 1b never refuses a short name an old Backlog: "
      f"line would match")

check("flow: step 1b dates the name when gh cannot answer the PR lookup",
      "<short-name>-<YYYY-MM-DD>" in flow_text,
      f"{FLOW_PATH} step 1b trusts a name the PR lookup could not check")

check("flow: step 1b checks a name with both of step 1's lookups",
      "both of step 1's lookups" in flat(flow_text),
      f"{FLOW_PATH} step 1b checks a name with fewer lookups than step 1 "
      f"uses to call it built, so a PR-body-only line slips through")

check("flow: step 1 deletes a backlog file whose feature already shipped",
      BACKLOG_BUILT_LINE in flat(flow_text),
      f"no line {BACKLOG_BUILT_LINE!r} in {FLOW_PATH}")

check("flow: step 1b offers chips on top of parking, never instead of it",
      "never instead of parking" in flow_text,
      f"{FLOW_PATH} never says chips come on top of parking, never instead")

flow_values = parsed.get("flow", (None, {}))[1]

check("flow: description says it accepts a backlog file path",
      "backlog" in flow_values.get("description", "").lower(),
      "flow's description never mentions accepting a backlog file path")

check("flow: argument-hint mentions the backlog path",
      "backlog" in flow_values.get("argument-hint", "").lower(),
      "flow's argument-hint never mentions a backlog file path")

FLOW_BACKLOG_TOOLS = [
    "Bash(gh label create:*)",
    "Bash(rm .devflow/backlog/*)",
    "Bash(git log:*)",
    "mcp__ccd_session__spawn_task",
]

for tool in FLOW_BACKLOG_TOOLS:
    check(f"flow: allowed-tools includes {tool}",
          tool in flow_values.get("allowed-tools", ""),
          f"flow's allowed-tools never lists {tool!r}")


# --------------------------- setup creates devflow:backlog beside devflow:plan
#
# `flow` files a parked feature under the `devflow:backlog` label, and the
# label has to exist before `flow` ever tries to use it -- `setup` is the one
# place that runs once per project, so it is the place that makes the label.
# The exact label command and the exact report line are pinned here for the
# same reason the flow backlog lines above are: a resumed run and a human
# both read them literally.

SETUP_PATH = os.path.join(SKILLS_DIR, "setup", "SKILL.md")
with open(SETUP_PATH, encoding="utf-8") as fh:
    setup_text = fh.read()

SETUP_BACKLOG_LABEL_CMD = (
    'gh label create devflow:backlog --description "A devflow parked feature" '
    "--color 5319E7"
)

check("setup: step 5 creates the devflow:backlog label beside devflow:plan",
      "gh label create devflow:plan" in setup_text
      and SETUP_BACKLOG_LABEL_CMD in setup_text,
      f"{SETUP_PATH} never runs {SETUP_BACKLOG_LABEL_CMD!r} after "
      f"'gh label create devflow:plan'")

check("setup: step 5 report line names both labels",
      "✓ **plans** github (labels devflow:plan, devflow:backlog exist)"
      in setup_text,
      f"{SETUP_PATH} never prints the exact "
      f"'✓ **plans** github (labels devflow:plan, devflow:backlog exist)' line")

check("setup: says flow parks extra features under the backlog label",
      re.search(r"[Pp]arks[^\n]*one feature per run", setup_text) is not None,
      f"{SETUP_PATH} never says flow parks extra features there, one "
      f"feature per run")


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

# The writer half of the Backlog: line -- see step 1b's chip checks above.

SUBMIT_BACKLOG_LINE = "Backlog: .devflow/backlog/<name>.md"

check("submit: a request that names a parked file gets a Backlog: line",
      "Also parked as" in submit_text and SUBMIT_BACKLOG_LINE in submit_text,
      f"{SUBMIT_PATH} never turns an 'Also parked as' request line into "
      f"{SUBMIT_BACKLOG_LINE!r} in the commit and the PR body")

check("submit: the Backlog: line goes in the commit and under What",
      re.search(r"Backlog:.*commit.*What|Backlog:.*What.*commit",
                flat(submit_text)) is not None,
      f"{SUBMIT_PATH} never says the Backlog: line goes in both the commit "
      f"body and the PR body's What")

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


# ----------------------------- submit ends with a recap of the run's own lines
#
# The step lines a run prints are scattered between whatever tool output sits
# between them, so a run is hard to read back once it is finished -- the
# reader has to scroll past every command's output to find the eight or nine
# lines that actually say what happened. The recap fixes that by repeating
# them, once, in one block, at the very end, right before the PR's link.

SUBMIT_RECAP_LINE = (
    "Before the PR link, repeat the lines this run printed — from the first, "
    "`flow`'s or `build`'s when they ran before you, through this one — in "
    "the order they were printed"
)

check("submit: step 9 prints a recap of the run's step lines before the PR link",
      SUBMIT_RECAP_LINE in flat(submit_text),
      f"no line {SUBMIT_RECAP_LINE!r} in {SUBMIT_PATH}. Without it the step "
      f"lines stay scattered between tool output, and a finished run is hard "
      f"to read back")

check("submit: the recap adds nothing new",
      "Add nothing to it" in submit_text,
      f"{SUBMIT_PATH} never says the recap adds no new text -- without that "
      f"rule it drifts into a second, competing summary of the run")


# ------------------------- a summary before the build, and one after the submit
#
# The size line says how big the work is, not what it will touch, so on Quick
# and Standard the human saw nothing of the change until it was built. flow now
# prints a short `todo` block right after the size line. Deep, where a wrong
# plan costs the most, puts that block in its one round of questions and waits,
# so a single "yes to all" answers the questions and approves the plan -- one
# stop, not two. At the other end the recap says how each step went but not
# what changed, which only the PR body said; submit prints a `done` block
# right above the recap.

FLOW_TODO_LINE = "→ **todo**"
FLOW_TODO_CARRY_ON = "Quick and Standard print it and carry on without waiting"
FLOW_TODO_DEEP_WAITS = (
    "Deep puts it in the same message as its round of questions, and waits"
)
FLOW_TODO_REDO = "show the new block and wait once more"
SUBMIT_DONE_LINE = "✓ **done**"
SUBMIT_DONE_ABOVE_RECAP = "right above the recap, and the recap leaves it out"

check("flow: prints a todo block after the size line",
      FLOW_TODO_LINE in flow_text,
      f"no {FLOW_TODO_LINE!r} line in {FLOW_PATH}. The size line alone never "
      f"says what the change will touch")

check("flow: Quick and Standard show the todo block without stopping",
      FLOW_TODO_CARRY_ON in flat(flow_text),
      f"{FLOW_PATH} never says Quick and Standard carry on past the todo block")

check("flow: Deep shows the todo block with its questions and waits",
      FLOW_TODO_DEEP_WAITS in flat(flow_text),
      f"{FLOW_PATH} never puts Deep's todo block in its question round -- "
      f"without it Deep either builds unchecked or stops twice")

check("flow: a changed answer shows the todo block again",
      FLOW_TODO_REDO in flat(flow_text),
      f"{FLOW_PATH} never re-shows the todo block when an answer changes the plan")

FLOW_DEEP_REPLY_LINE = (
    'Reply "yes to all" to take every recommendation and approve the todo '
    'block.'
)

check("flow: Deep's reply line tells the human it approves the plan too",
      FLOW_DEEP_REPLY_LINE in flow_text,
      f"no line {FLOW_DEEP_REPLY_LINE!r} in {FLOW_PATH}. The model knows one "
      f"reply approves the plan; the human replying would not")

check("submit: prints a done block of what changed",
      SUBMIT_DONE_LINE in submit_text,
      f"no {SUBMIT_DONE_LINE!r} line in {SUBMIT_PATH}. The recap says how the "
      f"steps went, not what changed")

check("submit: the done block sits above the recap, not inside it",
      SUBMIT_DONE_ABOVE_RECAP in flat(submit_text),
      f"{SUBMIT_PATH} never places the done block above the recap -- the recap "
      f"would repeat it, or the reader would find it after the link")


# ------------------------------- a line that is not a result takes the `→` mark
#
# `✓ **todo**` put the done mark on work that had not started, and
# `– **session** want it archived?` put the skipped mark on a question. Both
# read as results to a human skimming the marks. `→` is for a line that is
# not a result yet: work planned, or a call waiting on the human.

check("flow: the todo line is not marked done",
      "✓ **todo**" not in flow_text,
      f"{FLOW_PATH} still prints '✓ **todo**' -- the work has not started")

with open(os.path.join(SKILLS_DIR, "ship", "SKILL.md"), encoding="utf-8") as fh:
    SHIP_TEXT_FOR_MARKS = fh.read()

check("ship: the archive question takes the waiting mark",
      "→ **session** want it archived?" in SHIP_TEXT_FOR_MARKS
      and "– **session**" not in SHIP_TEXT_FOR_MARKS,
      "ship/SKILL.md marks the archive question as skipped, not waiting")

check("submit: the manual opinion offer is gone",
      "**opinion**" not in submit_text,
      f"{SUBMIT_PATH} still prints an '**opinion**' line -- the manual "
      f"/code-review, /security-review offer is meant to be retired now that "
      f"security-reviewer runs on its own")


# ------------------------------------------ a stop prints a shaped line too
#
# PR #38 shaped the lines a run prints when it goes well. The stops still
# said "say so in one line" with no mark and no label, so the line a human
# most needs to see -- the one that says the run did not finish -- was the
# one line with no shape to skim for.

STOP_LINES = {
    "build": ["✗ **stuck** 3 tries at <layer> — handing it back"],
    "tend": [
        "✗ **branch** <head branch> not checked out — <tree dirty, or why>",
        "✗ **pr** none open — devflow:submit comes first",
        "✗ **pr** no GitHub access — cannot read the PR",
        "✗ **stuck** <check> — 2 rounds, handing it back",
    ],
    "ship": [
        "✗ **pr** none open — devflow:submit comes first",
        "✗ **pr** no GitHub access — cannot read the PR",
        "✗ **live** <what you saw instead>",
        "✗ **branch** remote delete refused — <head branch> is yours to delete",
    ],
    "review": ["– **review** nothing to review since <fixed point>"],
    "setup": ["✗ **plans** label not made — gh said <the error>"],
}

for slug, lines in STOP_LINES.items():
    with open(os.path.join(SKILLS_DIR, slug, "SKILL.md"), encoding="utf-8") as fh:
        stop_text = fh.read()
    for line in lines:
        check(f"{slug}: prints the stop line {line!r}",
              line in stop_text,
              f"{slug}/SKILL.md never prints {line!r} where it stops")


# ------------------------------------- ship's report names the retargeted PRs
#
# `ship` step 6 promises "step 7 names the PRs you retargeted", and step 7's
# report template did not list them -- the final look on #26 found it, and it
# went under Known issues because that was the rule. The template line is
# pinned here so the promise and the report cannot drift apart again.

check("ship: the report names the PRs it retargeted",
      "**retargeted**" in ship_text,
      f"{SHIP_PATH} step 7 has no 'retargeted' line, so step 6's promise "
      f"that step 7 names them is not kept")


# --------------------------------- what is printed uses the reader's words
#
# `seam` and "both axes" are devflow's words, and they stay that way in the
# skills, which only the model reads. What reaches a human does not get to keep
# them. Two places print to someone who never read the skill that owns the
# word: `flow`'s chain report, where a piece's seam is labelled `tested at:`,
# and the PR body, where Evidence names both review axes and says what the
# final look asks of the reader.
#
# Glossing the word where the model reads it is the other fix, and it is the
# wrong one: it pays for every model read to help one human read. The label is
# pinned here instead, because a label in the reader's words is exactly what a
# later tidy-up folds back into the internal one.



evidence_review = [line for line in submit_text.split("\n")
                   if line.startswith("- Review:")]

check("submit: the Evidence Review line names both axes in plain words",
      any("built right" in line and "right thing" in line
          for line in evidence_review),
      f"{SUBMIT_PATH}: no '- Review:' line naming both 'built right' and "
      f"'right thing'. 'both axes ran' does not say which two, and the PR "
      f"reader never read the review skill")

check("submit: the Evidence Final look line says to read those lines yourself",
      "read those lines yourself" in flat(submit_text),
      f"{SUBMIT_PATH}: the 'Final look' line says 'unread by an agent' without "
      f"saying what that asks of the reader")

SEAM_LABEL = "`tested at:`"

check("flow: prints a piece's seam under a label the reader knows",
      SEAM_LABEL in flat(flow_text),
      f"{FLOW_PATH}: the chain loop never says to print the seam as "
      f"{SEAM_LABEL}. `seam` is this plugin's word, and step 3 is where it "
      f"would otherwise reach someone who never read this skill")

# Same rule as the lint self-test at the end of this file. `flat` widens what
# counts as a match, and a widened match that cannot miss is not a check.
check("flat self-test: finds a phrase the source wrapped",
      "read those lines yourself" in flat("unread by an agent, so read those\n"
                                          "  lines yourself (or: nothing new)"))

check("flat self-test: still misses a phrase that is not there",
      "read those lines yourself" not in flat("— unread by an agent (or: "
                                              "nothing new)"))


# ------------------------------ submit's step 6 has to leave a trace
#
# Every step of `submit` now prints one shaped line: step 1 `branch`, step 2
# `checks`, step 3 `debug`, step 4 `live`, step 5 `review`, step 7 `look`
# and `commit`, step 8 `pr`. Step 6, the docs one, printed nothing --
# so a run that skipped it and a run where nothing was stale produced identical
# output, in the transcript, in the commit and in the PR. Nobody could tell the
# two apart, the session itself included on a second pass. (Step 1 used to be
# silent too, before this piece, and was not the same case: a branch that is
# already correct has nothing to report, where step 6 always has either files
# or a clean look. Step 1 now prints unless `build` already put a branch
# line on screen this run, for the same reason.)
#
# It went wrong exactly that way on 22 Sep 2026: a follow-up pass on PR #31
# changed how `flow`'s step 0c behaves and updated none of `docs/flow.md`,
# `docs/provenance.md` or `README.md`. The reasoning survived only in a commit
# message, and the human caught it rather than the skill. Both forms of the line
# are pinned here for the same reason every other printed line in this file is:
# a prompt is the only place either of them lives.

# The shape, not the example. Which file the worked example names is the step's
# to change; `**docs** <a file> — <what was stale>` is the part a run
# reproduces. Pinning `README.md` here would fail the day someone picked a
# better example, with a message saying the line was missing when it was
# merely different -- the "test that punishes editing" this file's own `flat`
# docstring warns about.
DOCS_LINE_STALE = re.compile(r"\*\*docs\*\* \S+\.md — \S")

DOCS_LINE_CLEAN = "– **docs** nothing stale"

check("submit: step 6 prints what it changed",
      DOCS_LINE_STALE.search(flat(submit_text)) is not None,
      f"{SUBMIT_PATH} step 6 never shows a `docs:` line naming the file it "
      f"fixed and what was stale in it")

# This one is pinned verbatim, and the difference is not an inconsistency: it is
# the literal text a run prints when nothing was stale, so its wording is the
# rule. The line above is an example of a line whose content varies per run.
check("submit: step 6 prints even when nothing was stale",
      DOCS_LINE_CLEAN in flat(submit_text),
      f"no line {DOCS_LINE_CLEAN!r} in {SUBMIT_PATH}. Silence cannot mean both "
      f"'nothing was stale' and 'this step did not run'")

# One phrase, not two conjuncts. The first draft also asked for the word
# "skipped" anywhere in the file, which appears twice already at step 5 and in
# the PR template -- so that half could never fail, and a match that cannot miss
# is not a check. The file says so about `flat` a few lines up; it applies here.
check("submit: step 6 says why it prints at all",
      "cannot be told from a step that was skipped" in flat(submit_text),
      f"{SUBMIT_PATH} step 6 never says a step that prints nothing cannot be "
      f"told from one that was skipped — the reason is what makes the line a "
      f"step rather than a decoration, so it is pinned with the line")

check("submit: the Rules list carries the step 6 line",
      re.search(r"## Rules.*`docs`", submit_text, re.S) is not None,
      f"{SUBMIT_PATH}'s Rules list never mentions the `docs` line, so the one "
      f"step that had no output stays the one step with no rule either")

check("docs/submit: records why step 6 prints, citing #31",
      "#31" in docs_submit_text
      and "`docs`" in docs_submit_text,
      f"{DOCS_SUBMIT_PATH} does not cite the pull request whose follow-up pass "
      f"skipped step 6, so the reasoning lives only in the skill it constrains")


# ------------------------------ ship tends a conflict instead of stopping on it
#
# Step 2 refuses four things, and only one of them is ordinary: a conflict is
# what happens when another pull request merges first. `tend` already resolves
# one -- it merges the default branch in and reads both sides -- and it goes out
# through `build` and `submit`, so `review`'s two fresh agents read the
# resolution before it comes back. So `ship` hands that one over itself rather
# than making the human type the command, which is what they hit shipping #31
# and #32 on 23 Sep 2026: two branches cut from one commit, the second
# conflicting the moment the first landed.
#
# The other three stay stops, and that is the part most easily lost in a later
# tidy-up: a red check and a reviewer asking for changes are judgement calls,
# and a PR that is not OPEN is not shippable at all. Widening this to all four
# would turn `/devflow:ship` into something that answers reviewers.
#
# Three things are load-bearing and live only in the prompt: that it is the
# conflict case alone, that it runs once and never loops, and that the report
# says it happened. A resolution nobody announced, on a branch the human asked
# to have merged and not to have rewritten, is what these pins keep out.

# Not `CONFLICTING.*devflow:tend` with re.S, which was the first draft: step 2
# already named both, four lines apart, while refusing to run it. That pattern
# passed against the text it was meant to reject. The printed line is the thing
# only the new behaviour has.
SHIP_CONFLICT_LINE = "**conflict** handing #"

check("ship: hands a conflicting PR to tend rather than stopping",
      SHIP_CONFLICT_LINE in ship_text,
      f"{SHIP_PATH} step 2 never prints a '{SHIP_CONFLICT_LINE}...' line, so "
      f"nothing says it sends a CONFLICTING pull request to `devflow:tend` "
      f"itself rather than naming tend and stopping")

check("ship: still stops on the three that are not conflicts",
      "judgement call" in flat(ship_text),
      f"{SHIP_PATH} never says why a red check and a reviewer asking for "
      f"changes stay stops. Without the reason, the next edit widens the "
      f"handoff to all four and ship starts answering reviewers")

check("ship: tends a conflict once, and never loops",
      "one attempt" in flat(ship_text).lower(),
      f"{SHIP_PATH} never bounds the tend handoff to a single attempt. A "
      f"conflict tend could not fix is a conflict a second tend cannot either")

# The three below are the return path, and all three came out of the review of
# 23 Sep 2026, which found that coming back from `tend` branched on `mergeable`
# alone. `tend` pushes, and a push changes two things the first read cannot tell
# you: CI restarts, and GitHub recomputes mergeability asynchronously, answering
# `UNKNOWN` for the seconds right after -- which is exactly when this read lands.
# A return path reading one field would merge a PR with checks running, on the
# one step that cannot be undone.
#
# `hardcase` argued all three fell, on the grounds that the Rules list already
# forbids merging something red. It does. But the step says "carry on to step 3
# and merge", and this repo has already paid to learn that an implied step is
# the step that gets skipped -- that is what the `docs` line in `submit` exists
# for, and what the worktree-guard eval measured. A backstop in the Rules is not
# a substitute for the local line saying it.

check("ship: re-reads every condition after tend, not just mergeable",
      "all four conditions, not just `mergeable`" in flat(ship_text),
      f"{SHIP_PATH}'s return path from tend must re-run all four of step 2's "
      f"conditions. tend pushed, so CI restarted — branching on mergeability "
      f"alone merges a pull request whose checks are still running")

check("ship: does not read UNKNOWN mergeability as a yes",
      "It is not a yes" in flat(ship_text)
      and "UNKNOWN" in ship_text,
      f"{SHIP_PATH} never says an UNKNOWN mergeability is not clearance. "
      f"GitHub answers UNKNOWN for the first seconds after any push, and the "
      f"handoff guarantees a push immediately before this read")

check("ship: hands over only when the conflict is the only thing reported",
      "is not a conflict to hand over" in flat(ship_text),
      f"{SHIP_PATH} hands a PR to tend without checking it reports nothing "
      f"else. Conflicting and changes-requested together means tend answers "
      f"the reviewer too, which is not what a merge command was started for")

SHIP_TENDED_LINE = "**tended**"

check("ship: the report names a conflict it resolved on the way",
      SHIP_TENDED_LINE in ship_text,
      f"{SHIP_PATH} step 7 has no '{SHIP_TENDED_LINE}' line. The branch "
      f"changed between the human starting ship and the merge landing, and "
      f"the report is the only place that says so")

check("ship: keeps the boundary that nothing may call it",
      "disable-model-invocation: true" in ship_text
      and re.search(r"opposite direction", ship_text) is not None,
      f"{SHIP_PATH} must keep disable-model-invocation and say why calling "
      f"out to tend does not weaken it — a skill that reaches outward is not "
      f"a skill anything can reach into")

check("flow: still refuses to resolve a chain conflict itself",
      re.search(r"[Nn]ever resolve a merge conflict yourself", flow_text)
      is not None,
      f"{FLOW_PATH} lost its chain-conflict rule. A chain conflict means the "
      f"plan was wrong, so resolving it hides a planning bug — that reason is "
      f"untouched by ship tending a conflict against a moved default branch")

DOCS_SHIP_PATH = os.path.join(REPO_ROOT, "docs", "ship.md")
with open(DOCS_SHIP_PATH, encoding="utf-8") as fh:
    docs_ship_text = fh.read()

check("docs/ship: records why the conflict case alone is handed over",
      "devflow:tend" in docs_ship_text
      and re.search(r"CONFLICTING|conflict", docs_ship_text) is not None
      and "judgement" in flat(docs_ship_text),
      f"{DOCS_SHIP_PATH} never explains why the conflict is handed to tend "
      f"while the other three stay stops, so the reasoning lives only in the "
      f"skill it constrains")


# ------------------- and the folder the session itself is standing in
#
# The worktrees checked earlier are the builders'. This one is the session's
# own, and it exists because `build` cuts the feature branch with
# `git checkout -b`, which moves the *whole folder*. Two sessions open on one
# checkout share that folder, so the second one to start new work takes it, and
# the first finds its branch changed underneath it mid-build. Nothing announces
# that either. Size has nothing to do with it: a Quick typo fix moves the folder
# exactly as a Deep job does.
#
# So step 0c asks whether the folder is this session's to branch in, and moves
# into a worktree of its own when it is not. Several things live only in the
# prompt and are pinned here for the same reason the baseRef lines are: the two
# printed lines a human reads, the command that tells a linked worktree from the
# main checkout, the sentence that stops the model refusing EnterWorktree at the
# moment it fires, and the refusal to fall through into branching anyway.

WORKTREE_TAKEN_LINE = (
    "✓ **worktree** this folder is on <branch> — taking a checkout of my own"
)

WORKTREE_REFUSED_LINE = (
    "✗ **worktree** refused — this folder belongs to <branch>. "
    "Start again with: claude --worktree"
)

# Both pinned against `flat(flow_text)`, which already tolerates the wrap --
# WORKTREE_REFUSED_LINE prints as two physical lines so the shaped line stays
# at or under 80 visible columns, and flat() is what lets the period between
# them stand in for the line break.

check("flow: has a step 0c for the folder the session is standing in",
      "## Step 0c" in flow_text,
      f"{FLOW_PATH} has no '## Step 0c' section. New work runs "
      f"`git checkout -b`, which moves the whole folder out from under any "
      f"other session open on the same checkout")

check("flow: prints the worktree line word for word",
      WORKTREE_TAKEN_LINE in flat(flow_text),
      f"no line {WORKTREE_TAKEN_LINE!r} in {FLOW_PATH}. Moving a session into "
      f"its own checkout without saying so is the quiet kind of surprise this "
      f"whole step exists to stop")

check("flow: says what to do when the worktree is refused",
      WORKTREE_REFUSED_LINE in flat(flow_text),
      f"no line {WORKTREE_REFUSED_LINE!r} in {FLOW_PATH}. Without it the "
      f"refusal path falls through into branching in the shared folder, which "
      f"is the exact outcome step 0c exists to prevent")

check("flow: tells a linked worktree apart from the main checkout",
      "git rev-parse --path-format=absolute --git-dir --git-common-dir"
      in flow_text,
      f"{FLOW_PATH} never runs 'git rev-parse --path-format=absolute "
      f"--git-dir --git-common-dir'. A session already in a worktree owns its "
      f"folder, and must not be sent into a second one")

# The bare form is not a lesser version of the line above, it is the bug. Asked
# for without `--path-format=absolute`, git answers `--git-common-dir` relative
# to the current directory: from `docs/` in a plain checkout it prints `../.git`
# against an absolute `--git-dir`, which step 0c reads as "already in a
# worktree" and waves through. The whole guard then does nothing for any session
# started below the repo root, and says nothing while not doing it. Reproduced
# on git 2.49 and found by the review of 22 Sep 2026, which is why the absence
# of the broken form is pinned beside the presence of the working one.

check("flow: does not compare the two git dirs in their bare form",
      not re.search(r"git rev-parse --git-(dir|common-dir)\s*$",
                    flow_text, re.M),
      f"{FLOW_PATH} runs 'git rev-parse --git-dir' or '--git-common-dir' "
      f"bare. Those disagree in a plain checkout entered from a subdirectory, "
      f"so the guard skips exactly the folder it exists to protect")

check("flow: names EnterWorktree as the tool that moves the session",
      "EnterWorktree" in flow_text,
      f"{FLOW_PATH} never names the EnterWorktree tool")

check("flow: is itself the project instruction EnterWorktree asks for",
      "project instruction that tool asks for" in flat(flow_text),
      f"{FLOW_PATH} never says it is the instruction EnterWorktree requires. "
      f"That tool's own description says to use it only when the user or "
      f"project instructions asked for a worktree, so without this line it "
      f"gets refused at the moment it fires")

check("flow: never falls through to branching in a folder it does not own",
      re.search(r"[Dd]o not carry on in this folder", flow_text) is not None,
      f"{FLOW_PATH} never refuses to carry on in a folder that belongs to "
      f"another branch. A fallback that branches anyway is not a fallback")

check("flow: still has build cut the branch from the default ref in the worktree",
      "The worktree is a folder, not a base" in flat(flow_text),
      f"{FLOW_PATH} never says the worktree does not settle the base. With "
      f"worktree.baseRef = head the new checkout is cut from the very branch "
      f"this work has nothing to do with, so build must still be told to cut "
      f"from the default branch ref")

# `EnterWorktree` opens its worktree on a branch of its own, named after the
# worktree and cut from `HEAD` -- which in this step is always somebody else's
# branch. A session that reads that branch as its feature branch stops there,
# because `build`'s own rule is "already on a branch, keep it, whatever it is
# called". The first eval run of this case cut a proper branch in 2 of 4
# sessions, so the instruction to re-cut was landing about half the time. The
# trap gets named, and the line below is what names it: a step that prints
# something has done something, where a step that merely implies it has not.

WORKTREE_NOT_THE_BRANCH_LINE = (
    "✓ **worktree** on <its own branch> — build cuts fresh from "
    "<default branch ref>"
)

check("flow: says the worktree's own branch is not the feature branch",
      "is not your feature branch" in flat(flow_text),
      f"{FLOW_PATH} never says the branch EnterWorktree opens is not the "
      f"feature branch. build's rule is to keep the branch it finds, so an "
      f"unnamed trap is one the session walks into")

check("flow: prints what is still owed after entering the worktree",
      WORKTREE_NOT_THE_BRANCH_LINE in flat(flow_text),
      f"no line {WORKTREE_NOT_THE_BRANCH_LINE!r} in {FLOW_PATH}. Without it "
      f"the re-cut is implied rather than done, and the branch stays cut from "
      f"HEAD — which is the parked branch")

# Being in a linked worktree settles the folder, not the branch. With
# `worktree.baseRef` = "head", a worktree -- a chip's, or one the human opened
# with `claude --worktree` -- is cut from whatever the main checkout was on,
# and that can be a feature branch. Its branch is then ahead of the default
# branch ref with no PR, `build` keeps it, and the new PR carries the old
# feature's commits. So for new work, a worktree whose `Commits ahead` is not
# 0 has `build` re-cut from the default ref.
#
# The first version asked `git branch --contains HEAD` whether another branch
# held those commits, and kept the branch when none did. The review caught it:
# `git branch` lists local branches only, and `ship` deletes the local branch
# after a squash or rebase merge, so the borrowed commits then read as the
# worktree's own and ship twice. Where they came from never mattered -- step 0c
# only runs for new work, so they predate the request either way. The absence
# of that check is pinned beside the presence of the re-cut.

WORKTREE_CARRIES_LINE = (
    "✓ **worktree** <branch> carries commits — build re-cuts from "
    "<default branch ref>"
)

check("flow: re-cuts a worktree that already carries commits",
      WORKTREE_CARRIES_LINE in flat(flow_text),
      f"no line {WORKTREE_CARRIES_LINE!r} in {FLOW_PATH}. A worktree cut "
      f"from a feature branch looks like a clean start, build keeps it, and "
      f"the new PR carries the other branch's commits")

check("flow: does not ask which branches hold a worktree's commits",
      "git branch --contains" not in flow_text,
      f"{FLOW_PATH} runs `git branch --contains`. It sees local branches "
      f"only, so a source branch that was merged and deleted makes borrowed "
      f"commits look like the worktree's own")

check("flow: step 0c leaves a follow-up and a resume where they are",
      re.search(r"## Step 0c.*?[Oo]nly for new work", flow_text, re.S)
      is not None,
      f"{FLOW_PATH} step 0c never says it is for new work only. A follow-up "
      f"from step 0 and a resume from step 0b both belong on the branch this "
      f"folder is already on")

check("flow: the Rules list carries the shared-folder rule",
      re.search(r"## Rules.*folder that belongs to another", flow_text, re.S)
      is not None,
      f"{FLOW_PATH}'s Rules list never mentions branching in a folder that "
      f"belongs to another session")

check("flow: allowed-tools includes EnterWorktree",
      "EnterWorktree" in flow_values.get("allowed-tools", ""),
      "flow's allowed-tools never lists EnterWorktree")

DOCS_FLOW_PATH = os.path.join(REPO_ROOT, "docs", "flow.md")
with open(DOCS_FLOW_PATH, encoding="utf-8") as fh:
    docs_flow_text = fh.read()

check("docs/flow: records why the session takes a worktree of its own",
      "claude --worktree" in docs_flow_text
      and re.search(r"[Ss]tep 0c", docs_flow_text) is not None,
      f"{DOCS_FLOW_PATH} never explains step 0c next to the other worktree "
      f"rules, so the reasoning lives only in the skill it constrains")


# ------------------- a tended branch cannot be rebased, and ship has to know
#
# The two halves of the handoff fight each other, and both are right on their
# own. `tend` merges rather than rebases, because the branch is pushed and a
# reviewer may be reading it. That leaves a merge commit. Step 3 then reads
# "linear history and rebase allowed -> --rebase", which is true of any repo
# that keeps a linear history, so it picks the one method GitHub will refuse:
#
#     GraphQL: This branch can't be rebased (mergePullRequest)
#
# Not intermittent. The handoff *creates* the merge commit that *guarantees* the
# refusal, so every PR that goes through step 2 hits it. Found on 23 Sep 2026 by
# shipping #32 through the handoff on the day it merged -- the first real run of
# it, and it failed on the step after the one it changed.
#
# Three things are load-bearing and live only in the prompt: that the branch is
# asked about its shape before a method is chosen, that the question goes to the
# PR's branch rather than whichever one HEAD is on, and that a refusal is told
# apart from a failure worth retrying. Without the third, step 3's own
# instruction is "retry, with a wait", which here burns the cap and ends with
# the pull request unmerged.

# The fetch is load-bearing and reads as decoration, which is the combination
# that gets deleted. `git log --merges` reads a remote-tracking ref and nothing
# else in steps 1 or 3 updates one, so without it the guard has two silent
# failures rather than one. A ref last updated before `tend` pushed answers
# "empty" and waves the refusal through. A branch this clone has never seen is
# not a ref at all: git exits 128 with `unknown revision`, which is a guard that
# did not run. Both were reproduced on 23 Sep 2026 in a throwaway repo -- a clone
# taken before the branch existed, which is the ordinary case, since step 1 says
# the pull request need not be checked out to merge it.
#
# Pinned as adjacency rather than presence: `git fetch origin --prune` already
# appears further down, in the post-merge reconcile, so bare `git fetch origin`
# is a match that cannot miss.
#
# `[^\n]*` and not `\s*`, so the line may carry flags. The first draft demanded
# the bare form exactly, which would have failed `git fetch origin --prune` in
# front of the guard -- an equally correct fix, rejected for its spelling. That
# is the "test that punishes editing" this file's own `flat` docstring warns
# about, and it is worth naming twice because the fix looks like tightening.
check("ship: fetches before reading the branch's shape",
      re.search(r"git fetch origin[^\n]*\n\s*git log --merges", ship_text)
      is not None,
      f"{SHIP_PATH} step 3 reads origin/<head branch> without a `git fetch "
      f"origin` immediately before it. A stale ref answers 'empty' and a branch "
      f"this clone never fetched exits 128 — neither is the guard working")

check("ship: asks the branch's shape before choosing a merge method",
      "git log --merges" in ship_text,
      f"{SHIP_PATH} step 3 never runs 'git log --merges', so nothing notices a "
      f"merge commit before picking --rebase. tend puts one there every time it "
      f"resolves a conflict, and GitHub refuses to rebase a branch that has one")

# The remote ref is the correctness half, not a style preference. Step 1 says in
# as many words that the PR need not be checked out to merge, so `HEAD` is
# whatever branch this session happens to stand on -- `main`, most often, which
# has no merge commits ahead of itself and answers "empty" every time. A guard
# that reads the wrong branch and always says "no merge commit" is worse than no
# guard: it is silent, and it looks like it ran. Same shape as the bare
# `git rev-parse --git-dir` pin above, and pinned the same way, with the working
# form required and the broken one refused.
check("ship: asks about the PR's branch, not whichever one HEAD is on",
      re.search(r"git log --merges[^\n]*\.\.origin/", ship_text) is not None,
      f"{SHIP_PATH} does not run 'git log --merges' against origin/<head "
      f"branch>. Step 1 says the PR need not be checked out, so the branch to "
      f"ask about is the one step 1 wrote down, by name")

check("ship: does not ask HEAD whether the PR's branch has a merge commit",
      re.search(r"git log --merges[^\n]*\.\.HEAD", ship_text) is None,
      f"{SHIP_PATH} runs 'git log --merges ..HEAD'. HEAD is not the PR's "
      f"branch unless something checked it out, so that form answers 'empty' "
      f"from the default branch and waves the refusal straight through")

check("ship: drops rebase when the branch carries a merge commit",
      "off the table" in flat(ship_text),
      f"{SHIP_PATH} never says --rebase is off the table for a branch with a "
      f"merge commit. Finding the commit and choosing --rebase anyway is the "
      f"same bug with an extra command in front of it")

# The literal string GitHub answers with, because the table is only useful if it
# names the thing the reader will actually see on their screen. A paraphrase
# would be a row nobody matches against.
SHIP_REBASE_REFUSAL = "can't be rebased"

check("ship: names the refusal it will actually be shown",
      SHIP_REBASE_REFUSAL in ship_text,
      f"{SHIP_PATH}'s error table never quotes {SHIP_REBASE_REFUSAL!r}, the "
      f"text GitHub answers with. A table that does not name the error is one "
      f"nobody can match their own output against")

# Not "never retry" on its own, which would be a match that cannot miss: the
# Rules list has said "never retry a policy denial" since the retargeting work,
# four hundred lines away and about deleting a branch. The pair below is what
# only the new state has -- a refusal is deterministic where 500 and 503 are
# transient, and that distinction is the whole reason the third row exists.
check("ship: tells a refusal apart from a failure worth retrying",
      "deterministic" in flat(ship_text)
      and "transient" in flat(ship_text),
      f"{SHIP_PATH} never separates a deterministic refusal from a transient "
      f"failure. Both leave the default branch unmoved, so the SHA cannot tell "
      f"them apart and 'retry, with a wait' runs the cap out for nothing")

check("ship: the Rules list carries the refusal rule",
      re.search(r"## Rules.*refusal", ship_text, re.S) is not None,
      f"{SHIP_PATH}'s Rules list never mentions a refusal, so the one error "
      f"state that must not be retried is the one with no rule against it")

# Both conjuncts have to be able to miss, and the first draft's second one could
# not: bare `rebase` was already in docs/ship.md twice before this change, in the
# step 6 section about a local `git branch -d`. It would have passed against text
# that said nothing about any of this. `can't be rebased` is the forge's own
# words and arrived with this change, so it fails when the explanation goes.
check("docs/ship: records why a tended branch cannot be rebased",
      "merge commit" in docs_ship_text
      and "can't be rebased" in docs_ship_text,
      f"{DOCS_SHIP_PATH} never explains that tend's merge is what rules out a "
      f"rebase, so the next person to tidy step 3's ladder puts --rebase back "
      f"at the top with nothing to tell them why it was moved")


# ------------------------------- ship deploys only from a checkout it may move
#
# A Deploy line deploys a checkout: `wrangler deploy` ships the folder it runs
# in, and this repo's `claude plugin update` copies the root folder. So that
# checkout has to be at the merged commit, and step 4 never said so. When ship
# made it so for PR #42 on 24 Sep 2026, by detaching the root at origin/main,
# it moved the folder underneath another session that had an uncommitted edit
# there -- the edit later became PR #43. Ship may move a checkout only when
# nobody is in it: clean, and on no branch.

check("ship: the deploy runs from a checkout at the merged commit",
      "must be at the merged commit" in flat(ship_text),
      f"{SHIP_PATH} never says the deploy's checkout has to hold the merge")

check("ship: moves that checkout only when it is clean, detached or on the "
      "default branch",
      "It is free when `status` prints nothing and the folder is on no branch "
      "or on the default branch" in flat(ship_text)
      and "git checkout --detach <default branch ref>" in ship_text,
      f"{SHIP_PATH} never limits the move to a checkout nobody is using")

# A clean main checkout sits on `main` far more often than detached, and the
# rule above stopped every deploy of this repo for it (24 Sep 2026, after
# #47). Moving `main` forward with --ff-only keeps the folder on its branch,
# as a git pull would. Any other branch is still someone's work, and a
# fast-forward that fails means `main` holds local commits: also someone's.

check("ship: moves a clean default-branch folder with --ff-only",
      "Free and on the default branch" in flat(ship_text)
      and "git merge --ff-only <default branch ref>" in ship_text,
      f"{SHIP_PATH} never moves a clean folder on the default branch forward")

check("ship: a failed fast-forward stops the deploy, never forced",
      "a fast-forward that fails" in flat(ship_text)
      and "never force it" in flat(ship_text),
      f"{SHIP_PATH} never says what to do when --ff-only is refused")

# --ff-only refuses only a branch that has diverged. One that is ahead of the
# ref -- someone pulled the merge, then committed -- says "Already up to date"
# and exits 0, and the deploy would ship their commit. Found by the review of
# this change. So the folder has to land exactly on the ref.
check("ship: checks the default-branch folder landed exactly on the ref",
      "Then compare `git rev-parse HEAD` with `git rev-parse <default branch "
      "ref>`" in flat(ship_text)
      and "Already up to date" in ship_text,
      f"{SHIP_PATH} deploys a default branch that is ahead of the remote")

check("ship: any other branch, or unpushed commits, still stops the deploy",
      "a change, any other branch, or commits the remote does not have"
      in flat(ship_text),
      f"{SHIP_PATH} lets a folder on a feature branch, or one holding "
      f"unpushed commits, be moved")

check("docs/ship: records why the default branch is free",
      "--ff-only" in docs_ship_text and "#47" in docs_ship_text
      and "Already up to date" in docs_ship_text,
      f"{DOCS_SHIP_PATH} never says why a clean default-branch folder may "
      f"move, or why --ff-only alone is not enough")

check("ship: leaves its worktree before asking another checkout",
      "the harness refuses `git -C`" in flat(ship_text)
      and "git -C <folder>" not in ship_text,
      f"{SHIP_PATH} asks another checkout with git -C, which a worktree "
      f"session is refused")

check("ship: fetches after the merge before comparing against the ref",
      "`<default branch ref>` is stale until you do" in flat(ship_text),
      f"{SHIP_PATH} compares the deploy checkout against a ref fetched before "
      f"the merge")

check("ship: a folder already at the ref is still checked for someone's work",
      "whether or not it is already at the ref" in flat(ship_text),
      f"{SHIP_PATH} deploys from a folder with someone's uncommitted edit as "
      f"long as it is already at the ref")

check("ship: its own folder is detached, not read as someone else's work",
      "The folder this session is in" in ship_text
      and "or the main checkout when it started there" in flat(ship_text),
      f"{SHIP_PATH} reads its own worktree on the merged head branch as "
      f"another session's work")

check("ship: an in-use checkout stops every Deploy line, from anywhere",
      "no `Deploy` line runs, from this folder or any other" in flat(ship_text),
      f"{SHIP_PATH} leaves room to run the deploy from another folder")

check("ship: stops the deploy when the checkout is in use",
      "✗ **deploy** <folder> in use — <its branch, or its changes>; deploy it yourself"
      in ship_text,
      f"{SHIP_PATH} never prints the in-use stop line")

check("docs/ship: records why ship stopped moving a checkout in use",
      "#42" in docs_ship_text and "#43" in docs_ship_text
      and "in use" in docs_ship_text,
      f"{DOCS_SHIP_PATH} never records the #42 deploy that moved #43's folder")


# ------------------------------------- this repo's Deploy block hits the root
#
# A local-scope install is one entry per folder, keyed to the folder the update
# runs in. On 24 Sep 2026 the update ran in a worktree after PR #47, said it
# had updated, and left the main checkout's entry on the old commit. The old
# Verify line, `test -d` on the cache directory, passed anyway: the directory
# exists as soon as any folder updates. So the Deploy line goes to the main
# checkout first, and Verify asks for the main checkout's entry by commit.

CLAUDE_MD_PATH = os.path.join(REPO_ROOT, "CLAUDE.md")
with open(CLAUDE_MD_PATH, encoding="utf-8") as fh:
    claude_md_text = fh.read()

deploy_block = claude_md_text.split("## Deploy", 1)[-1].split("\n## ", 1)[0]
deploy_lines = re.findall(r"^- Deploy: (.+)$", deploy_block, re.M)
verify_lines = re.findall(r"^- Verify: (.+)$", deploy_block, re.M)

MAIN_CHECKOUT = ('"$(dirname "$(git rev-parse --path-format=absolute '
                 '--git-common-dir)")"')

check("CLAUDE.md: the Deploy line runs the update in the main checkout",
      deploy_lines == [f"cd {MAIN_CHECKOUT} && claude plugin update "
                       f"devflow@eddiechok-devflow --scope local"],
      f"{CLAUDE_MD_PATH} runs the update wherever ship stands, which updates "
      f"only that folder's install")


def run_verify(entries):
    """Run the Verify line against a fake ~/.claude holding these entries.

    The merge's cache directory is always there, as it is once any folder
    has updated -- which is why its presence proves nothing.
    """
    with tempfile.TemporaryDirectory() as home:
        plugins = os.path.join(home, ".claude", "plugins")
        os.makedirs(os.path.join(plugins, "cache", "eddiechok-devflow",
                                 "devflow", _merged[:12]))
        with open(os.path.join(plugins, "installed_plugins.json"), "w") as fh:
            json.dump({"plugins": {"devflow@eddiechok-devflow": entries}}, fh)
        env = dict(os.environ, HOME=home)
        return subprocess.run(["bash", "-c", verify_lines[0]], cwd=REPO_ROOT,
                              env=env, capture_output=True).returncode


_git = lambda *a: subprocess.run(["git", *a], cwd=REPO_ROOT, text=True,
                                 capture_output=True).stdout.strip()
_main_checkout = os.path.dirname(
    _git("rev-parse", "--path-format=absolute", "--git-common-dir"))
# --verify, and the exit code read: a bare rev-parse of a missing ref prints
# the name back, and every run_verify check would then compare "origin/main"
# with itself and pass.
_merged_run = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                              "origin/main^{commit}"], cwd=REPO_ROOT,
                             text=True, capture_output=True)
_merged = _merged_run.stdout.strip() if _merged_run.returncode == 0 else ""

if len(verify_lines) != 1 or not _merged:
    check("CLAUDE.md: has one Verify line, and origin/main to check it by",
          False, f"{len(verify_lines)} Verify line(s) in {CLAUDE_MD_PATH}, "
          f"origin/main {'found' if _merged else 'missing -- fetch it'}")
else:
    check("CLAUDE.md: Verify passes when the main checkout has the merge",
          run_verify([{"scope": "local", "projectPath": _main_checkout,
                       "gitCommitSha": _merged}]) == 0,
          f"{CLAUDE_MD_PATH} Verify fails on a correct install")
    check("CLAUDE.md: Verify fails when the main checkout is on an old commit",
          run_verify([{"scope": "local", "projectPath": _main_checkout,
                       "gitCommitSha": "0" * 40}]) != 0,
          f"{CLAUDE_MD_PATH} Verify passes while the main checkout is stale")
    check("CLAUDE.md: Verify fails when only a worktree has the merge",
          run_verify([{"scope": "local",
                       "projectPath": os.path.join(_main_checkout, ".claude",
                                                   "worktrees", "x"),
                       "gitCommitSha": _merged}]) != 0,
          f"{CLAUDE_MD_PATH} Verify passes when a worktree updated and the "
          f"main checkout did not")

check("CLAUDE.md: says each folder has its own local-scope install",
      "one entry per folder" in flat(deploy_block),
      f"{CLAUDE_MD_PATH} never says why the update must run in the main "
      f"checkout")


# ------------------------------- ship deletes the branches it can prove are empty
#
# Rebase and squash rewrite a branch's commits, so `git branch -d` refuses it
# even when every line is on the default branch, and step 6 used to forbid `-D`
# outright. Every squash or rebase merge ended with a local branch the human
# had to delete by hand -- #40 and #41 both did. The forge knows exactly which
# commit it merged, so the check can be precise instead of forbidden: a branch
# whose tip is that commit holds nothing the merge did not carry. The session's
# own worktree branch is the same shape: flow's step 0c opens it and build cuts
# the feature branch elsewhere, so a tip still where it was created is empty.

check("ship: reads the merged head commit from the forge",
      "headRefOid" in ship_text,
      f"{SHIP_PATH} never asks the forge which commit it merged")

check("ship: force-deletes the head branch only when its tip is that commit",
      "tip is the PR's `headRefOid`" in flat(ship_text),
      f"{SHIP_PATH} never ties the forced delete to the merged head commit")

check("ship: a tip behind the merged head is empty too, not kept",
      "git merge-base --is-ancestor <head branch> <headRefOid>" in ship_text,
      f"{SHIP_PATH} keeps a branch that is only behind the merged head -- a "
      f"commit added on GitHub makes it look like unpushed work")

check("ship: removes the session's worktree before its checked-out head branch",
      "git refuses to delete a branch that is checked out" in flat(ship_text),
      f"{SHIP_PATH} deletes the head branch while the worktree still has it "
      f"checked out")

check("ship: never moves the main checkout it returns to after the worktree",
      "the folder you land in is the one `flow`'s step 0c left alone" in flat(ship_text)
      and "switch to the default branch and fast-forward it first" not in ship_text,
      f"{SHIP_PATH} still switches the folder it lands in after ExitWorktree")

check("ship: keeps a head branch that holds commits the merge did not carry",
      "✗ **branch** <head branch> kept — it has commits the merge did not carry"
      in ship_text,
      f"{SHIP_PATH} never prints the kept-branch line")

check("ship: removes the session's worktree and its empty branch",
      "still the commit it was created from" in flat(ship_text)
      and "git reflog" in ship_text,
      f"{SHIP_PATH} never proves the worktree branch empty from its reflog")

check("ship: allowed-tools includes ExitWorktree",
      "ExitWorktree" in ship_text.split("---")[1],
      f"{SHIP_PATH} cannot leave the worktree it is about to remove")

check("ship: the Rules list forbids a forced delete it has not proven",
      "Never force-delete a branch you have not proven" in ship_text
      and "to silence a warning" not in ship_text,
      f"{SHIP_PATH}'s Rules still forbid -D outright, or allow it unproven")

check("docs/ship: records why the forced delete is safe",
      "headRefOid" in docs_ship_text,
      f"{DOCS_SHIP_PATH} never explains the merged-head check")


# ------------------------------------------- one shape for every printed line
#
# Before this piece a step's output had no common shape: some printed
# `label: text`, some printed prose, and some main-path steps printed nothing
# at all, so a skipped step read exactly like a clean one. Every human-facing
# skill now carries the same `## Output` section, word for word, so the shape
# is one fact stated once rather than seven separate promises that drift
# apart the first time one of them is edited. Pinned here for the same reason
# every other cross-file promise in this suite is: a phrase that is only in
# the prompt is a phrase a later edit can quietly break in one of the seven
# and never in the other six.

OUTPUT_SECTION = """## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR."""

HUMAN_FACING_SKILLS = ["flow", "build", "submit", "review", "tend", "ship", "setup"]

human_facing_text = {}
for slug in HUMAN_FACING_SKILLS:
    with open(os.path.join(SKILLS_DIR, slug, "SKILL.md"), encoding="utf-8") as fh:
        human_facing_text[slug] = fh.read()

for slug, text in human_facing_text.items():
    check(f"{slug}: carries the ## Output section word for word",
          OUTPUT_SECTION in text,
          f"{slug}/SKILL.md is missing the exact '## Output' section shared, "
          f"word for word, by all seven human-facing skills")


# ------------------------------ build prints red and green as their own labels

# The gate lines used to read `✗ **test** red -- fails for the right reason`
# and `✓ **test** green -- 1 passed, exit 0`. The first puts a fail mark on a
# gate that is supposed to fail, so a session skimming for `✗` cannot tell
# "RED failed the way it's meant to" from a real failure. Splitting red and
# green into their own labels removes that ambiguity.

BUILD_PATH = os.path.join(SKILLS_DIR, "build", "SKILL.md")
build_text = human_facing_text["build"]

BUILD_RED_LINE = "✓ **red** 22 new pins fail — the lines are not in the skills yet"
BUILD_GREEN_LINE = "✓ **green** 22 new pins pass, 271 in all, exit 0"

check("build: verify-RED prints its own red label",
      BUILD_RED_LINE in build_text,
      f"{BUILD_PATH} never prints {BUILD_RED_LINE!r} after verify-RED")

check("build: verify-GREEN prints its own green label",
      BUILD_GREEN_LINE in build_text,
      f"{BUILD_PATH} never prints {BUILD_GREEN_LINE!r} after verify-GREEN")

check("build: no longer marks the expected-to-fail RED gate as a failure",
      "✗ **test** red" not in build_text,
      f"{BUILD_PATH} still prints '✗ **test** red', which reads as a real "
      f"failure for a gate that is supposed to fail")

check("build: no longer uses the bare test label for the green gate",
      "✓ **test** green" not in build_text,
      f"{BUILD_PATH} still prints '✓ **test** green' instead of the "
      f"red/green label split")


# -------------------------------- one fixed label list for every shaped line

# `flow`'s chain report already glosses a word for the human it reaches --
# `seam:` where every skill's own text says "tested at". A printed label is
# the same risk running the other way: nothing stopped two skills from
# picking two different words for the same idea, or one skill's label
# drifting a piece at a time with nobody able to see the other six at once.
# The list lives here, once, read by this test and nowhere else -- never in
# a skill body, which a model rereads on every single run.
#
# Every label already on this list is a lowercase run of letters with no
# internal space; a hyphen inside one, like `no-behaviour`, still reads and
# matches as a single token. `no-behaviour` keeps its hyphen because it is
# also the hand-off argument name `submit` passes `review`, word for word --
# renaming the label without renaming the argument would split one idea into
# two spellings, which is the exact drift this list exists to catch.

SHAPED_LABELS = {
    "backlog", "branch", "chains", "checks", "chips", "cleaned", "commit",
    "conflict", "debug", "deploy", "docs", "done", "features", "glossary",
    "green", "handback", "lint", "live", "look", "merge", "merged",
    "no-behaviour", "open", "opinion", "override", "parked", "piece",
    "plan", "plans", "pr", "pushed", "red", "retargeted", "review",
    "session", "settings", "stuck", "tended", "test", "theirs", "todo",
    "typecheck",
    "worktree", "yours",
}

# `→` also runs mid-sentence in prose -- "Either fails → **stop editing**" --
# and that is not a printed line, so `→` counts only where it opens a line or a
# backtick citation. The other three marks still count anywhere.
SHAPED_LINE_LABEL = re.compile(
    r"(?:[✓✗–]|(?:^|`)[ \t]*→) \*\*([^*\n]+)\*\*", re.M)


def shaped_labels_in(text):
    return set(SHAPED_LINE_LABEL.findall(text))


check("label scanner: finds a listed label",
      "checks" in shaped_labels_in("✓ **checks** 3 of 3 pass, exit 0"))

check("label scanner: finds a label that is not on the list",
      "madeup" in shaped_labels_in("✓ **madeup** something")
      and "madeup" not in SHAPED_LABELS)

check("label scanner: a list item or quote with an old mark is still scanned",
      {"madeup", "other"} <= shaped_labels_in(
          "- ✓ **madeup** x\n> ✗ **other** y"))

check("label scanner: a prose arrow before bold text is not a label",
      not shaped_labels_in("Either fails → **stop editing** and say so"))

check("label scanner: finds an indented or cited waiting line",
      {"todo", "session"} <= shaped_labels_in(
          "   → **todo** a thing\nthen print `→ **session** want it archived?`"))

check("label scanner: finds a label that is not lowercase letters",
      {"Merged", "pr2", "final look"} <= shaped_labels_in(
          "✓ **Merged** #2\n✓ **pr2** #3\n– **final look** nothing new"))

for slug, text in human_facing_text.items():
    unlisted = sorted(shaped_labels_in(text) - SHAPED_LABELS)
    check(f"{slug}: every shaped line uses a label from the fixed list",
          not unlisted,
          f"{slug}/SKILL.md prints a shaped line whose label is not in "
          f"SHAPED_LABELS: {unlisted}")


# --------------------------- no shaped example line is longer than 80 columns

# A line a human reads wraps in a narrow terminal or a chat pane past 80
# columns, and the wrap lands wherever the window happens to be, not wherever
# reads well. Two shapes carry a shaped example in these files: its own line,
# usually fenced, and a line citing it inline mid-sentence -- "print `✓
# **label** ...`, then ...". Both are text a human will see printed verbatim,
# so both are checked. `**` is markdown, invisible once rendered, and does
# not count; a `<placeholder>` counts exactly as written, because that is
# what a reader sees before the run fills it in.

SHAPED_STANDALONE_LINE = re.compile(
    r"^[ \t]*([✓✗–→] \*\*[^*\n]+\*\*.*)$", re.M)
SHAPED_INLINE_CITATION = re.compile(
    r"`([✓✗–→] \*\*[^*\n]+\*\*[^`]*)`")


def shaped_example_lines(text):
    found = set()
    found.update(SHAPED_STANDALONE_LINE.findall(text))
    found.update(SHAPED_INLINE_CITATION.findall(text))
    return found


def visible_length(example):
    # A citation pulled from running prose can carry the paragraph's own
    # soft-wrap -- a literal newline where the rendered line only ever had a
    # space. Collapse whitespace the way a reader would before measuring.
    return len(re.sub(r"\s+", " ", example.strip()).replace("**", ""))


check("line-length scanner: counts a listed label's line, ** not counted",
      visible_length("✓ **checks** 3 of 3 pass, exit 0") == 28)

check("line-length scanner: a <placeholder> counts as written",
      visible_length("✓ **branch** <name>") == len("✓ branch <name>"))

check("line-length scanner: finds a line over 80 columns",
      visible_length("✓ **label** " + ("x" * 80)) > 80)

for slug, text in human_facing_text.items():
    too_long = sorted(
        (visible_length(example), example)
        for example in shaped_example_lines(text)
        if visible_length(example) > 80
    )
    check(f"{slug}: every shaped example line is 80 visible characters or fewer",
          not too_long,
          f"{slug}/SKILL.md has shaped example line(s) over 80 visible "
          f"characters: {too_long}")


# ---------------------------------- a line says what happened, not which step
#
# `✓ **red** fails for the right reason` read the rule back to the human and
# told them nothing about this run; so did `✓ **checks** build's run stands`
# and `✓ **review** both axes ran`. Each now leads with the result. And the
# recap, which repeated all ~32 lines of a run, now leaves out the routine
# ones whose result is the same on almost every run, so what is left is news.

check("build: the red line no longer reads the rule back",
      "✓ **red** fails for the right reason" not in build_text,
      f"{BUILD_PATH} still prints '✓ **red** fails for the right reason'")

check("build: the green line carries the tests only, not the lint",
      "lint" in flat(build_text).split(BUILD_GREEN_LINE)[0][-200:],
      f"{BUILD_PATH} never says, just above the green line, that the lint is "
      f"not part of it")

SUBMIT_CHECKS_STAND = "✓ **checks** <n> of <n> pass, exit 0 — build's run, no edit since"
check("submit: the checks-stand line leads with the result",
      SUBMIT_CHECKS_STAND in submit_text
      and "build's run stands, no edit since" not in submit_text,
      f"{SUBMIT_PATH} never prints {SUBMIT_CHECKS_STAND!r}")

SUBMIT_REVIEW_LINE = (
    "✓ **review** 2 found, 2 fixed — a loose test scanner, a stop line with no mark"
)
check("submit: the review line names what was found",
      SUBMIT_REVIEW_LINE in submit_text
      and "✓ **review** both axes ran" not in submit_text,
      f"{SUBMIT_PATH} never prints {SUBMIT_REVIEW_LINE!r}")

check("submit: prints no second branch line after build's",
      "unless `build` printed one this run" in flat(submit_text),
      f"{SUBMIT_PATH} prints '✓ **branch**' again after build already did")

SUBMIT_RECAP_ROUTINE = [
    "`– **pr** none found`", "`✓ **branch**`", "a green `✓ **checks**`",
    "`✓ **debug** none found`", "`– **look** nothing changed`",
    "`✓ **handback**`",
]
check("submit: the recap leaves out the routine lines",
      all(item in submit_text for item in SUBMIT_RECAP_ROUTINE),
      f"{SUBMIT_PATH} never names every routine line the recap leaves out: "
      f"{SUBMIT_RECAP_ROUTINE}")

check("submit: the recap keeps every ✗ and → line",
      "Every `✗` and `→` line stays" in submit_text,
      f"{SUBMIT_PATH} never says the recap keeps every ✗ and → line")


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

# --------------------------------------- agents/security-reviewer's report shape
#
# `security-reviewer` reviews as an attacker only, and its report has to name
# an exploit case rather than a rule violation, or it is just `reviewer` with
# a different name. Pinned here so an edit that drifts the sections or the
# bar fails loudly instead of quietly turning it into a second code-quality
# pass.

SECURITY_REVIEWER_PATH = os.path.join(AGENTS_DIR, "security-reviewer.md")
with open(SECURITY_REVIEWER_PATH, encoding="utf-8") as fh:
    security_reviewer_text = fh.read()

check("agents/security-reviewer: report carries ## Exploitable",
      "## Exploitable" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never pins the '## Exploitable' report section")

check("agents/security-reviewer: report carries ## Reviewed",
      "## Reviewed" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never pins the '## Reviewed' report section")

check("agents/security-reviewer: names the Not reported: line",
      "Not reported:" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never pins the 'Not reported:' line for when "
      f"the word limit bit")

check("agents/security-reviewer: pins the exploit-only bar",
      "who, what input, what they get" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never pins the exploit bar in these words -- "
      f"who, what input, what they get")

DOCS_PROVENANCE_PATH = os.path.join(REPO_ROOT, "docs", "provenance.md")
with open(DOCS_PROVENANCE_PATH, encoding="utf-8") as fh:
    docs_provenance_text = fh.read()

check("docs/provenance: credits claude-code-security-review with its star count",
      "anthropics/claude-code-security-review" in docs_provenance_text
      and "6,262 stars" in docs_provenance_text,
      f"{DOCS_PROVENANCE_PATH} does not credit "
      f"anthropics/claude-code-security-review with its star count")

# ------------------------------------ review spawns security-reviewer on the
# ------------------------------------ danger list, and widens hardcase's job
#
# `security-reviewer` does not run on every change. `reviewer` already reads
# the danger list on every review, so its report is where `review` reads the
# spawn condition from. Five items start it; the other three items on the
# same list are still worth a human's attention but do not.

SECURITY_ITEMS = ("auth and permissions, secrets and keys, payments, "
                   "public API or wire format, CI/CD config")
NON_SECURITY_ITEMS = ("database migrations, deleting or weakening tests, "
                       "anything that cannot be reverted")

REVIEWER_PATH = os.path.join(AGENTS_DIR, "reviewer.md")
with open(REVIEWER_PATH, encoding="utf-8") as fh:
    reviewer_text = fh.read()

check("agents/reviewer: danger list names the five security items",
      SECURITY_ITEMS in flat(reviewer_text),
      f"{REVIEWER_PATH} never lists the five items in these words -- "
      f"{SECURITY_ITEMS!r}")

check("agents/reviewer: danger list keeps the three non-security items",
      NON_SECURITY_ITEMS in flat(reviewer_text),
      f"{REVIEWER_PATH} never lists the three items in these words -- "
      f"{NON_SECURITY_ITEMS!r}")

REVIEW_SKILL_PATH = os.path.join(SKILLS_DIR, "review", "SKILL.md")
with open(REVIEW_SKILL_PATH, encoding="utf-8") as fh:
    review_skill_text = fh.read()

check("review: starts security-reviewer only on the five security items",
      ("Start `devflow:security-reviewer` only when that line names one of "
       "five items: " + SECURITY_ITEMS) in flat(review_skill_text),
      f"{REVIEW_SKILL_PATH} never pins the spawn condition in these words")

check("review: hardcase is handed security-reviewer's findings too",
      "`reviewer`'s findings, and `security-reviewer`'s findings when it ran"
      in flat(review_skill_text),
      f"{REVIEW_SKILL_PATH} never hands hardcase security-reviewer's findings")

check("review: step 4 report carries a ## Security section",
      "## Security" in review_skill_text,
      f"{REVIEW_SKILL_PATH} never pins a '## Security' report section")

check("review: Worst of each carries a Security line",
      "- Security:" in review_skill_text,
      f"{REVIEW_SKILL_PATH} never pins a 'Security:' line under Worst of each")

HARDCASE_PATH = os.path.join(AGENTS_DIR, "hardcase.md")
with open(HARDCASE_PATH, encoding="utf-8") as fh:
    hardcase_text = fh.read()

check("hardcase: accepts security-reviewer's findings",
      "security-reviewer" in hardcase_text and "## Exploitable" in hardcase_text,
      f"{HARDCASE_PATH} never says it is handed security-reviewer's findings "
      f"under '## Exploitable'")

DOCS_REVIEW_PATH = os.path.join(REPO_ROOT, "docs", "review.md")
with open(DOCS_REVIEW_PATH, encoding="utf-8") as fh:
    docs_review_text = fh.read()

check("docs/review: the agent table lists security-reviewer",
      "`security-reviewer`" in docs_review_text,
      f"{DOCS_REVIEW_PATH} never lists security-reviewer in the agent table")

# ---------------------------- submit treats Exploitable findings like Blocking
# ---------------------------- and drops the manual security-review offer
#
# `security-reviewer` now runs on its own whenever the danger list calls for
# it, so a human forgetting to type `/security-review` is no longer the gate.
# Pinned here so a later edit cannot quietly bring the manual offer back.

check("submit: step 5 treats Exploitable findings like Blocking",
      "**Blocking**, **Exploitable**, **Missing** and **Built wrong**"
      in flat(submit_text),
      f"{SUBMIT_PATH} never folds security-reviewer's Exploitable findings "
      f"in with Blocking")

check("submit: round 2 for the security axis is scoped to security-reviewer",
      "`devflow:security-reviewer` for its own" in flat(submit_text),
      f"{SUBMIT_PATH} never scopes round 2 to devflow:security-reviewer")

check("submit: Evidence names which axes ran, were NOT RUN, or skipped",
      "which were `NOT RUN`, and which were `skipped`" in flat(submit_text),
      f"{SUBMIT_PATH} never says Evidence names NOT RUN and skipped axes")

check("docs/submit: records why the manual opinion offer was retired",
      "security-reviewer" in docs_submit_text
      and "opinion" in docs_submit_text.lower(),
      f"{DOCS_SUBMIT_PATH} never explains why the /code-review, "
      f"/security-review offer is gone")

# --------------------------------------- README and flow no longer tell a
# --------------------------------------- human to run /security-review
#
# `security-reviewer` runs on its own now. Nothing under `skills/` or in
# README.md may still read as a hand-off to a slash command a human has to
# remember to type.

README_PATH = os.path.join(REPO_ROOT, "README.md")
with open(README_PATH, encoding="utf-8") as fh:
    readme_text = fh.read()

check("README: never tells the human to run /security-review",
      "/security-review" not in readme_text,
      f"{README_PATH} still names /security-review")

check("README: the agents paragraph names security-reviewer",
      "`security-reviewer`" in readme_text,
      f"{README_PATH} never names security-reviewer among the review agents")

for slug in HUMAN_FACING_SKILLS:
    text = human_facing_text[slug]
    check(f"{slug}: never tells the human to run /security-review",
          "/security-review" not in text,
          f"{slug}/SKILL.md still names /security-review")

check("flow: the danger list line says review will include security-reviewer",
      "The first five are security items: when one matched, say plainly that "
      "the review will include `security-reviewer`"
      in flat(flow_text),
      f"{FLOW_PATH} never pins that line -- the danger list still reads as "
      f"a human's job")

# ------------------------------------------ what round 1 of the review missed
#
# Round 1 of this branch's own review found four gaps: flow promised the
# security pass on all eight danger-list items when only five start it; the
# decision was made once, so a fix that added an auth check after round 1
# shipped with no security pass; nothing said a bug both agents report is one
# finding; and two of the request's own examples were not named in the
# checklist.

check("flow: the five security items come first in the danger list",
      flow_text.index("- CI/CD configuration")
      < flow_text.index("- database schema or data migrations"),
      f"{FLOW_PATH} lists migrations among the first five, which it calls the "
      f"security items")

check("submit: a later reviewer report can still start security-reviewer",
      "The last read decides the security pass, not the first" in submit_text,
      f"{SUBMIT_PATH} decides the security pass once, from round 1 only")

check("submit: a bug both agents report is fixed once",
      "One bug, one fix" in submit_text,
      f"{SUBMIT_PATH} never says a finding both agents report is one finding")

check("agents/security-reviewer: names data that is not the caller's",
      "data that is not the caller's" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never names access to another user's data")

check("agents/security-reviewer: names secrets leaking to the client",
      "sent to the client" in security_reviewer_text,
      f"{SECURITY_REVIEWER_PATH} never names secrets leaking in an error or "
      f"response sent to the client")

check("review: its description names the security pass",
      "can it be attacked" in human_facing_text["review"].split("---")[1],
      "review/SKILL.md's description still describes two axes only")


# --------------------------- plan and backlog issues go through REST
#
# A cloud session reaches GitHub through a proxy that answers every GraphQL
# request with a 403. `gh issue list`, `gh issue view` and `gh issue create`
# all send GraphQL -- `create` too, before it posts anything -- so on a
# `github` project every plan and backlog issue failed there, and the run fell
# back to a file. REST through `gh api` gets through, and so does
# `gh label create`. Tested in a cloud session on 24 Sep 2026.

REVIEW_PATH = os.path.join(SKILLS_DIR, "review", "SKILL.md")
review_skill_text = human_facing_text["review"]

PLAN_LIST_REST = "issues?labels=devflow:plan&state=open"

for slug, text in (("flow", flow_text), ("review", review_skill_text)):
    check(f"{slug}: lists plan issues through REST",
          PLAN_LIST_REST in text and "select(.pull_request | not)" in text,
          f"{slug}/SKILL.md never lists plan issues with gh api "
          f"'repos/{{owner}}/{{repo}}/{PLAN_LIST_REST}' and a filter that "
          f"drops pull requests")

for slug, text in (("flow", flow_text), ("review", review_skill_text),
                   ("setup", setup_text)):
    body = text.split("---", 2)[2]
    check(f"{slug}: never runs gh issue list, view or create",
          re.search(r"gh issue (list|view|create)\b", body) is None,
          f"{slug}/SKILL.md still names a GraphQL issue command, which a "
          f"cloud session's proxy refuses")

check("flow: step 4 opens the plan issue through REST",
      "-F body=@<body file> -f 'labels[]=devflow:plan'" in flow_text,
      f"{FLOW_PATH} never opens the plan issue with gh api and "
      f"-F body=@<body file> -f 'labels[]=devflow:plan'")

for slug, text in (("flow", flow_text), ("review", review_skill_text)):
    check(f"{slug}: says what to do when gh cannot fill {{owner}}/{{repo}}",
          "cannot fill `{owner}/{repo}`" in flat(text),
          f"{slug}/SKILL.md never says to write the owner and repo in when "
          f"gh cannot fill the placeholder")

check("flow: reads a request issue through REST",
      "gh api repos/{owner}/{repo}/issues/NUMBER --jq .body" in flow_text,
      f"{FLOW_PATH} never reads a #123 request with gh api")

check("review: reads a Closes issue through REST",
      re.search(r"\*\*An issue\*\*[^\n]*gh api repos/\{owner\}/\{repo\}"
                r"/issues/<n> --jq \.body", review_skill_text) is not None,
      "review/SKILL.md never reads the issue a commit closes with gh api")

# `gh api` takes any method and any path, and a prefix rule cannot narrow
# either, so pre-approving it would let text in an issue body reach an admin
# write with no prompt. It stays behind the permission prompt. The GraphQL
# issue commands it replaced go too, since nothing runs them any more.
for slug in ("flow", "review"):
    tools = parsed.get(slug, (None, {}))[1].get("allowed-tools", "")
    check(f"{slug}: allowed-tools never pre-approves gh api",
          "gh api" not in tools,
          f"{slug}'s allowed-tools pre-approves gh api, every method and path")
    check(f"{slug}: allowed-tools drops the GraphQL issue commands",
          "gh issue" not in tools,
          f"{slug}'s allowed-tools still lists a gh issue command")

SETUP_PROOF_CMD = "gh api 'repos/{owner}/{repo}/issues?per_page=1' --jq length"

check("setup: proves the tracker with a REST read",
      SETUP_PROOF_CMD in setup_text,
      f"{SETUP_PATH} never runs {SETUP_PROOF_CMD!r}")

GH_INSTALL_LINE = "apt-get update && apt-get install -y gh"

check("setup: names the setup-script line that installs gh",
      GH_INSTALL_LINE in setup_text,
      f"{SETUP_PATH} never names {GH_INSTALL_LINE!r}")

check("setup: no longer says the web has no gh",
      "has no `gh`" not in setup_text,
      f"{SETUP_PATH} still says the web sandbox has no gh")

DOCS_WEB_PATH = os.path.join(REPO_ROOT, "docs", "web.md")
with open(DOCS_WEB_PATH, encoding="utf-8") as fh:
    docs_web_text = flat(fh.read())
DOCS_FLOW_PATH = os.path.join(REPO_ROOT, "docs", "flow.md")
with open(DOCS_FLOW_PATH, encoding="utf-8") as fh:
    docs_flow_text = flat(fh.read())

check("docs/web: names the setup-script line that installs gh",
      GH_INSTALL_LINE in docs_web_text,
      f"{DOCS_WEB_PATH} never names {GH_INSTALL_LINE!r}")

check("docs/web: says the proxy refuses every GraphQL request",
      "every GraphQL request" in docs_web_text,
      f"{DOCS_WEB_PATH} still says only some GraphQL fields are refused")

check("docs/web: makes no untested claim about the setup-script cache",
      "cache keeps it" not in docs_web_text,
      f"{DOCS_WEB_PATH} claims the setup script's cache keeps gh; untested")

check("docs/web: no longer says gh comes up authenticated",
      "comes up already authenticated" not in docs_web_text,
      f"{DOCS_WEB_PATH} still says an installed gh just works")

check("docs/flow: no longer says the web has no gh",
      "has no `gh`" not in docs_flow_text,
      f"{DOCS_FLOW_PATH} still says the web sandbox has no gh")

check("docs/provenance: records the cloud test of 24 Sep",
      "the cloud test of 24 Sep" in docs_provenance_text,
      f"{DOCS_PROVENANCE_PATH} has no row citing the cloud test of 24 Sep")


# --------------------------- a curl fallback when gh is not installed
#
# A cloud session whose setup script does not install gh still reaches
# GitHub: GH_TOKEN holds a placeholder the proxy swaps for the real
# credential, and plain curl to api.github.com came back 200 in the cloud
# test of 24 Sep. So a missing gh falls back to curl before it falls back to
# a file. The token is the danger here: it goes to api.github.com only, and
# it is never printed.

CURL_AUTH = 'curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN"'
CURL_ISSUES = "https://api.github.com/repos/<owner>/<repo>/issues"

check("flow: falls back to curl when gh is not installed",
      "command -v gh" in flow_text and CURL_AUTH in flow_text
      and CURL_ISSUES in flow_text,
      f"{FLOW_PATH} never gives the curl form for a missing gh")

check("flow: the curl fallback reads owner and repo from the remote",
      "git remote get-url origin" in flow_text,
      f"{FLOW_PATH} never says where curl gets <owner>/<repo> from")

check("flow: the curl fallback builds the issue as JSON, not by hand",
      "json.dumps" in flow_text
      and "--data-binary @<json file>" in flow_text,
      f"{FLOW_PATH} never builds the POST body with json.dumps")

check("flow: every issue call points at the curl form",
      flat(flow_text).count("the `curl` form in step 0b") >= 3,
      f"{FLOW_PATH} names the curl form fewer than three times: the request "
      f"read, the backlog create and the plan create each need it")

for slug, text in (("flow", flow_text), ("review", review_skill_text),
                   ("setup", setup_text)):
    check(f"{slug}: never prints the token, never sends it elsewhere",
          "Never print `$GH_TOKEN`" in flat(text)
          and "api.github.com" in text and "no other host" in flat(text),
          f"{slug}/SKILL.md gives a curl form without the token rule")

check("review: lists plan issues with curl when gh is missing",
      CURL_AUTH in review_skill_text
      and "https://api.github.com/repos/<owner>/<repo>/issues?labels=devflow:plan"
      in review_skill_text,
      "review/SKILL.md has no curl form for a missing gh")

check("setup: proves the tracker with curl when gh is missing",
      CURL_AUTH in setup_text
      and "https://api.github.com/repos/<owner>/<repo>/issues?per_page=1"
      in setup_text,
      f"{SETUP_PATH} has no curl proof read for a missing gh")

for slug in ("flow", "review"):
    tools = parsed.get(slug, (None, {}))[1].get("allowed-tools", "")
    check(f"{slug}: allowed-tools never pre-approves curl",
          "curl" not in tools,
          f"{slug}'s allowed-tools pre-approves curl, which carries the token")

check("docs/web: names the curl fallback",
      "falls back to `curl`" in docs_web_text,
      f"{DOCS_WEB_PATH} never says a missing gh falls back to curl")

check("setup: makes the labels with curl when gh is missing",
      "https://api.github.com/repos/<owner>/<repo>/labels" in setup_text,
      f"{SETUP_PATH} has a curl read but no curl label create, so setup "
      f"stops at the label with no gh")

check("setup: no longer says a missing gh goes straight to a file",
      "Without it, runs on the web fall back to a local file"
      not in flat(setup_text),
      f"{SETUP_PATH} still says a missing gh means a file; curl comes first")

check("docs/web: no longer says plans on GitHub need gh",
      "Plans on GitHub need `gh` here" not in docs_web_text,
      f"{DOCS_WEB_PATH} still says a plan issue cannot be read without gh")

for slug, text in (("review", review_skill_text), ("setup", setup_text)):
    check(f"{slug}: says what curl does when the remote names no repo",
          "If the remote does not name a GitHub repo" in flat(text),
          f"{slug}/SKILL.md never says to write the owner and repo in when "
          f"the git remote does not name them")

# ------------------------------ a leftover bug is parked, not only noted
#
# Known issues held three kinds of line, and only one of them is work: a bug
# the bounded loop left open. #24, #26 and #33 each named one -- a real bug, a
# one-line fix written out -- in a merged PR body that nothing ever read
# again. Rejected findings and test gaps are notes for whoever merges, and a
# tracker full of them is noise. So submit parks the leftover bugs the way
# flow step 1b parks a feature, and links each from its Known issues line.

check("submit: names the three kinds of Known issue",
      all(k in submit_text for k in
          ("**A rejected finding**", "**A test gap**", "**A leftover bug**")),
      f"{SUBMIT_PATH} never sorts Known issues into rejected findings, test "
      f"gaps and leftover bugs")

check("submit: only a leftover bug is parked",
      "Only a leftover bug is parked" in flat(submit_text),
      f"{SUBMIT_PATH} never says rejected findings and test gaps stay in the "
      f"PR body alone")

check("submit: parks a leftover bug as a devflow:backlog issue",
      "labels[]=devflow:backlog" in submit_text,
      f"{SUBMIT_PATH} has no gh api call filing a devflow:backlog issue")

check("submit: falls back to a backlog file",
      ".devflow/backlog/<short-name>.md" in submit_text,
      f"{SUBMIT_PATH} never writes a backlog file when there is no tracker")

check("submit: parks before the commit, so a backlog file ships in the PR",
      "Park them before the commit" in flat(submit_text),
      f"{SUBMIT_PATH} never says the parking happens before step 7's commit")

check("submit: the Known issues line links to what it was parked as",
      "— parked as #" in submit_text,
      f"{SUBMIT_PATH} never shows a Known issues line linking its backlog item")

check("submit: an update does not park the same bug twice",
      "already links" in flat(submit_text),
      f"{SUBMIT_PATH} never says a bug the PR body already links is not "
      f"filed again on an update")

# Round 1 of review: parking came after step 7's last check run, so a backlog
# file was committed unchecked; and the only guard against filing twice read a
# PR body that does not exist yet when step 8 was blocked on an earlier run.

check("submit: a backlog file written at step 7 gets the checks run again",
      "A backlog file is an edit" in flat(submit_text),
      f"{SUBMIT_PATH} commits a backlog file no check run has seen")

check("submit: looks for an existing backlog item before parking",
      "labels=devflow:backlog" in submit_text
      and "Found on: <this branch>" in submit_text
      and "Never park the same bug twice" in flat(submit_text),
      f"{SUBMIT_PATH} only guards against a second filing through the PR "
      f"body, which a blocked step 8 never wrote")

# The review after merging main: the issue body used a fixed /tmp path, which
# main had just taken off the PR body for the same reason, and the lookup read
# only the first 30 backlog issues, so an older one parked from another branch
# was never matched.

check("submit: makes the backlog issue body with mktemp",
      'mktemp "${TMPDIR:-/tmp}/devflow-backlog.XXXXXX"' in submit_text
      and "/tmp/devflow-backlog.md" not in submit_text,
      f"{SUBMIT_PATH} still writes the backlog issue body to a fixed path")

check("submit: reads every page of the backlog issues",
      "gh api --paginate 'repos/{owner}/{repo}/issues?labels=devflow:backlog"
      in submit_text,
      f"{SUBMIT_PATH} lists only the first page of devflow:backlog issues")

check("submit: prints a parked line",
      "✓ **parked** #" in submit_text,
      f"{SUBMIT_PATH} never prints what it parked")

check("docs/submit: says why leftover bugs are parked, citing #24, #26, #33",
      all(f"#{n}" in docs_submit_text for n in (24, 26, 33))
      and "leftover bug" in docs_submit_text,
      f"{DOCS_SUBMIT_PATH} does not explain parking leftover bugs")

# --------------------------- pull request calls go through REST too
#
# The same cloud test found `gh pr list` and `gh pr view` refused with the
# same 403: every `gh pr` command sends GraphQL. So `flow`, `tend` and
# `submit` reach pull requests through `gh api`, exactly as the plan and
# backlog issues above do. `ship` keeps `gh pr`: it is a local skill, and
# docs/web.md says so. REST forms tested against this repo and cli/cli on
# 24 Sep 2026. `gh` fills `{owner}` and `{repo}` in the path only, never in
# a `-f` value, which is why the search query sits in the path.

tend_text = human_facing_text["tend"]
submit_text = human_facing_text["submit"]
TEND_PATH = os.path.join(SKILLS_DIR, "tend", "SKILL.md")

PR_BY_HEAD = "gh api 'repos/{owner}/{repo}/pulls?head={owner}%3A<branch>&state="

# The colon is written %3A. `gh` still fills the old `:owner`, `:repo` and
# `:branch` placeholders and drops the colon, so `head={owner}:repo-cleanup`
# went out as `head=eddiechokagent-devflow-cleanup`, GitHub ignored the
# malformed filter, and the call returned 30 unrelated PRs. Found by the
# review of this change, 24 Sep 2026.

for slug, text in (("flow", flow_text), ("tend", tend_text),
                   ("submit", submit_text)):
    body = text.split("---", 2)[2]
    check(f"{slug}: never runs a gh pr command",
          re.search(r"gh pr [a-z]", body) is None,
          f"{slug}/SKILL.md still names a gh pr command, which sends "
          f"GraphQL a cloud session's proxy refuses")
    check(f"{slug}: finds the branch's PR through REST",
          PR_BY_HEAD in text,
          f"{slug}/SKILL.md never asks {PR_BY_HEAD!r}")
    check(f"{slug}: never writes the head filter's colon bare",
          "head={owner}:" not in text,
          f"{slug}/SKILL.md writes head={{owner}}:, which gh reads as an "
          f"old placeholder on a branch named repo-*, owner-* or branch-*")
    tools = parsed.get(slug, (None, {}))[1].get("allowed-tools", "")
    check(f"{slug}: allowed-tools never pre-approves gh api",
          "gh api" not in tools,
          f"{slug}'s allowed-tools pre-approves gh api, every method and path")
    check(f"{slug}: allowed-tools drops the GraphQL pr commands",
          "gh pr" not in tools,
          f"{slug}'s allowed-tools still lists a gh pr command")

check("flow: step 0 tells merged from closed from the REST answer",
      'if .merged_at then "MERGED"' in flow_text,
      f"{FLOW_PATH} step 0 never turns merged_at into MERGED; REST says "
      f"closed for both")

check("flow: says gh fills the placeholders in the path only",
      "never in a `-f` value" in flat(flow_text),
      f"{FLOW_PATH} never says why the search query sits in the path")

# tend's PR line was an injected `gh pr view`. An injected `gh api` would
# need gh api in allowed-tools, and a failed permission check aborts the
# whole skill (docs/tend.md), so the line leaves the Context block and the
# read moves into step 1.
check("tend: no PR lookup in the Context block",
      "- PR: !`" not in tend_text,
      f"{TEND_PATH} still injects a PR lookup at load time")

# The lists are paged 30 at a time, oldest first, so a PR with 31 reviews
# hid its newest verdict on page 2. Every list tend reads takes --paginate.
TEND_REST = [
    "gh api repos/{owner}/{repo}/pulls/<n> --jq",
    "git fetch origin <head branch>",
    "git switch <head branch>",
    "gh api --paginate 'repos/{owner}/{repo}/commits/<sha>/check-runs",
    "commits/<sha>/status",
    "gh api --paginate repos/{owner}/{repo}/pulls/<n>/reviews",
    "gh api --paginate repos/{owner}/{repo}/pulls/<n>/comments",
]
for cmd in TEND_REST:
    check(f"tend: reads the PR with {cmd!r}",
          cmd in tend_text,
          f"no {cmd!r} in {TEND_PATH}")

check("tend: stops on a PR from a fork",
      ".head.repo.full_name != .base.repo.full_name" in tend_text,
      f"{TEND_PATH} never checks whether the PR's head is a fork it cannot "
      f"push to")

check("tend: reads a conflict the way REST reports it",
      "`mergeable_state` of `dirty`" in flat(tend_text)
      and "CONFLICTING" not in tend_text,
      f"{TEND_PATH} still reads a conflict as CONFLICTING, which only "
      f"GraphQL says")

# The body file comes from mktemp. A fixed /tmp path let two sessions
# overwrite each other's body, and let another user on the machine plant
# the file first and write the PR body. Found by the review of this change.
# The template carries its own X's: GNU mktemp -t refuses a name without
# them, and a cloud session runs Linux.
SUBMIT_OPEN = ("gh api repos/{owner}/{repo}/pulls -f title=\"<subject>\" "
               "-F body=@<body file> -f head=<branch> "
               "-f base=<default branch>")
SUBMIT_UPDATE = ("gh api -X PATCH repos/{owner}/{repo}/pulls/<n> "
                 "-F body=@<body file>")

check("submit: makes the PR body file with mktemp",
      'mktemp "${TMPDIR:-/tmp}/devflow-pr.XXXXXX"' in submit_text
      and "/tmp/devflow-pr.md" not in submit_text,
      f"{SUBMIT_PATH} writes the PR body to a fixed path another session "
      f"or user can reach first")

# The same for flow's issue bodies: the plan, each parked feature, and the
# JSON the curl fallback posts. Each file is made fresh with mktemp, and no
# skill that files an issue names a fixed /tmp/devflow- path.
for kind in ("plan", "backlog", "issue"):
    check(f"flow: makes the {kind} file with mktemp",
          f'mktemp "${{TMPDIR:-/tmp}}/devflow-{kind}.XXXXXX"' in flow_text,
          f"{FLOW_PATH} writes the {kind} file to a fixed path another "
          f"session or user can reach first")

for slug, text in (("flow", flow_text), ("review", review_skill_text),
                   ("setup", setup_text), ("submit", submit_text)):
    check(f"{slug}: names no fixed /tmp/devflow- path",
          re.search(r"/tmp/devflow-[\w-]+\.(md|json)", text) is None,
          f"{slug}/SKILL.md still writes to a fixed /tmp path")

for cmd in (SUBMIT_OPEN, SUBMIT_UPDATE):
    check(f"submit: step 8 runs {cmd!r}",
          cmd in submit_text,
          f"no {cmd!r} in {SUBMIT_PATH}")

check("docs/web: no longer says the gh pr commands still send GraphQL",
      "still send GraphQL" not in docs_web_text,
      f"{DOCS_WEB_PATH} still says submit and tend send GraphQL")

check("docs/web: says ship keeps gh pr because it is local",
      "`ship` keeps `gh pr`" in docs_web_text,
      f"{DOCS_WEB_PATH} never says why ship was left on gh pr")

# --------------------------------------------------------------------- report

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)

