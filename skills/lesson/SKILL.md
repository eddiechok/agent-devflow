---
name: lesson
description: "Use to record one line about devflow itself - a mistake, a piece of waste, or an idea - so a later review can spot a pattern across runs. Writes one line to the private eddiechok/devflow-lessons repo. Started by hand with a short text, or called by another skill with the skill, kind, what went wrong, proof and the human's own words. Never edits a skill itself; a human approves every skill change."
argument-hint: "[idea] \"<text>\""
---

# lesson

One line, to one repo, never to a skill.

Why these rules are what they are: [docs/lessons.md](../../docs/lessons.md). Read it only
if a rule looks wrong.

## What kind of lesson this is

A **devflow lesson** is about this plugin — `flow` sized something wrong, a reviewer's
finding fell to `hardcase`, a deploy's `Verify` line failed, a run wasted turns. That is
what this skill records.

**A fact about the current project is not a devflow lesson.** "The tests need the sandbox
key" goes into that project's `CLAUDE.md` through `submit`, in the same PR as the work
that found it out — never here, and never into `~/.claude` either. The session that did
the run sorts each lesson; no subagent does.

## Input

By hand:

```
/devflow:lesson "flow sized the checkout change Quick, it was Deep"
/devflow:lesson idea "the PR body could carry a screenshot"
```

The first shape is kind `mistake`. `idea` as the first word makes the kind `idea`. There
is no by-hand shape for kind `waste` — waste is counted from saved sessions, by
`devflow:lesson-review`, not typed in.

Called by another skill — `flow`, `review`, `ship` — with five things it already knows:
the skill the lesson is about, the kind, what went wrong, the proof, and the human's own
words when they corrected it.

## The line

One line, seven parts, appended to `lessons.md`:

```
YYYY-MM-DD | <project> | <skill> | <kind> | <what> | <proof> | "<human's words>"
```

- **Date** — today, `YYYY-MM-DD`.
- **Project** — the repo name from `git remote get-url origin` (the last path segment,
  `.git` stripped), else this folder's name when there is no remote.
- **Skill** — the devflow skill the lesson is about: `flow`, `build`, `review`, `ship`,
  `submit`, `tend`, or whichever one called `lesson`.
- **Kind** — `mistake`, `waste`, or `idea`.
- **What** — what went wrong, or the idea, in a few words.
- **Proof** — a PR or commit link that backs the line up, or `none`.
- **Human's words** — the human's own words when they corrected it, quoted; `—` when there
  were none.

**A `|` inside any part becomes `/`** before the line is built, so a stray pipe in a
commit message or a human's own sentence can never split the line into the wrong number
of parts.

## Writing it

The repo is hard-coded: `eddiechok/devflow-lessons`, file `lessons.md`, branch `main`. No
env var, no config — the human chose this over one.

**With `gh` (the Mac path):**

```
gh api repos/eddiechok/devflow-lessons/contents/lessons.md
```

Read the current content and its `sha`. Decode the content, append the new line, and PUT
it back with that `sha`:

```
gh api -X PUT repos/eddiechok/devflow-lessons/contents/lessons.md \
  -f message="lesson: <skill> <kind>" -f content=<base64> -f sha=<sha>
```

If the file does not exist yet (a 404 on the read), PUT it with no `sha` to create it. If
the PUT is rejected for a stale `sha` — another write landed first — re-read the file and
retry once with the fresh `sha`. A second conflict falls through to the fallback below.

**With no `gh` (the web path):** use the `add_repo` tool for `eddiechok/devflow-lessons`,
then:

```
git clone <the repo> <a mktemp -d dir>
```

Append the line, commit, and `git push` to `main`. On a rejected push, `git pull --rebase`
and retry once. Remove the temporary directory when you are done, whether it worked or
not.

**If every path fails** — no `gh`, `add_repo` fails, or the retried write still fails —
print the line so the human can copy it by hand:

```
✗ **lesson** could not reach eddiechok/devflow-lessons — copy this line:
2026-10-02 | shop-repo | build | mistake | wrote the test after the code | shop-repo#12 | "test first, always"
```

## Success

Exactly one line, and nothing else:

```
✓ **lesson** recorded — flow mistake
```

## Rules

- Never write a lesson into the current project, and never into `~/.claude`. The lessons
  repo is the only destination.
- Never edit a skill. A human approves every skill change; this skill only ever collects
  the evidence for `devflow:lesson-review` to propose one later.
- A fact about this project is not a devflow lesson — that goes to the project's
  `CLAUDE.md`, through `submit`, in the same PR as the work that found it.
- Never guess a `sha` or overwrite one you did not just read. A stale write loses whatever
  another session just appended.
- Never print more than the one success line, or more than the fallback line and the
  line itself when every write failed.
