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

# ------------------------------------------- cross-check against a real parser

try:
    import yaml
except ImportError:
    yaml = None

if yaml is None:
    print("\nnote: PyYAML not importable, so the parser cross-check was skipped.\n"
          "      The lint above ran regardless and is the load-bearing part.\n")
else:
    for slug, (fm, values) in parsed.items():
        loaded = yaml.safe_load(fm) or {}
        for key, value in values.items():
            check(f"{slug}: {key} round-trips through PyYAML",
                  str(loaded.get(key, "")) == literal(value),
                  f"on disk {literal(value)[-60:]!r}\n"
                  f"     parsed  {str(loaded.get(key, ''))[-60:]!r}")

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
