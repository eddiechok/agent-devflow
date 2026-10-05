# The report

`flow` step 3, `plan`'s check against the todo and `submit`'s last step print a report:
a rule above and below, a `###` title, and a `####` heading per section. A section with
nothing in it is left out.

## Plan — before the first edit

```markdown
---

### 📋 Plan — waiting for your go

**Size:** Standard — build prints its own red and green

#### What changes

| # | Change | Where |
|---|---|---|
| 1 | build prints red and green as their own lines | `skills/build/SKILL.md` |
| 2 | its pins follow | `skills/test-frontmatter.py` |

#### What you will see

- a failing test shows its red line before any code is written

#### Tracker

- comment on #12 with the PR link

---
```

- **What changes** — one row per change, and where it lands.
- **What you will see** — what the user will notice. A change nobody can see says
  `- nothing changes for the user`.
- **Tracker** — one line per tracker action: closing, labelling or commenting on an issue.
- Quick does not wait, so its title is `### 📋 Plan`.

## Pieces — a plan that matches the todo

```markdown
---

### 🧩 Pieces — starting the builders

**Checked against:** the plan you approved. Nothing changed.

| # | Chain | Piece |
|---|---|---|
| 1 | A | Add the storage column and migration |
| 2 | A | Read it in the settings API |
| 3 | B | Rate-limit the public search endpoint |

**Runs:** A and B at the same time.

---
```

## Plan, changed — a plan that drifted

The Plan report again, titled `### 📋 Plan, changed after planning — waiting for your go`,
with one more line under the size: `**What changed:** <the row added, dropped or changed>`.

## Done — the end of the run

`submit` prints it at step 9, right before the PR link. Its rows are the plan's rows —
the last Plan report this run printed: the one the human said go to, or Quick's, which
needs no go — in the same order, with a mark each: `✓` done, `✗` not done. Each `✗` row gets one `**Not done:**` line under the table that says why.
No plan printed this run — `tend`, or `submit` started by hand — means the rows are what
this branch changed, each `✓`.

```markdown
---

### ✅ Done

#### What changed

| # | Change | Where | |
|---|---|---|---|
| 1 | build prints red and green as their own lines | `skills/build/SKILL.md` | ✓ |
| 2 | its pins follow | `skills/test-frontmatter.py` | ✗ |

**Not done:** 2 — the pins went in the PR before this one

#### What you will see

- a failing test shows its red line before any code is written

#### Check it yourself

1. `python3 skills/test-frontmatter.py`
2. Run `/devflow:build` on a small change and look for the red line

#### Assumptions

- Took the recommendation on X, because no answer was given

#### Tracker

- ✓ closes #12 when the PR merges

#### Needs you

✗ **live** the settings page did not load

---
```

- **What changed** — no size line: the plan said it.
- **What you will see** — what the branch now does, in words a user of it would know, not
  the file list. One to three bullets.
- **Check it yourself** — the steps under the PR body's How to check this yourself, word
  for word. The `**live**` line is not shown: a passing one is noise, and a failing one is
  a `✗` line, which goes under Needs you.
- **Assumptions** — the PR body's Assumptions, word for word.
- **Tracker** — each tracker action, with its result.
- **Needs you** — every `✗` and `→` line this run printed that is still open, from the
  first, `flow`'s or `build`'s when they ran before `submit`, and every item under the PR
  body's Known issues, and nothing else. A `✗` that a later line this run settled — a
  check that went green again, a finding that was fixed — is left out. A clean run has no
  Needs you.
