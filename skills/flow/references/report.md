# The report

`flow` step 3 and `plan`'s check against the todo print a report: a rule above and below,
a `###` title, and a `####` heading per section. A section with nothing in it is left out.

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
