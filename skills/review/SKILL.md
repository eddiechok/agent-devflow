---
name: review
description: "Use when a branch needs reviewing before it becomes a pull request, or when you want a read on work you did not write. Reviews everything between a fixed point and now along two axes, kept apart on purpose - is it built right, and is it the right thing - and, when the danger list names a security item, can it be attacked. It also runs each review agent the project named in CLAUDE.md. Each axis runs in a fresh agent that never sees this session's reasoning. Called by submit at step 5, and safe to start yourself on any branch."
argument-hint: "[fixed point - a branch, tag or SHA. Defaults to the branch point] [request: the words the human typed, for step 2] [no-behaviour: build's reason, on its own line]"
allowed-tools: Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git symbolic-ref:*)
---

# review

Two axes, a security pass when the danger list calls for one, fresh agents, no blending.

Why these rules are what they are: [docs/review.md](../../docs/review.md). Read it only if a
rule looks wrong.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- Changed files: !`git status --short 2>/dev/null || true`

## 1. Pin the fixed point

`$ARGUMENTS` has three optional parts, in this order: a fixed point, then `request:` followed by the request text, then a `no-behaviour:` line. The fixed point is the first word **only if that word is neither `request:` nor `no-behaviour:`**. Everything after `request:` is text for step 2 — up to a `no-behaviour:` line if `submit` passed one — never a ref, never resolved. No fixed point, or `$ARGUMENTS` that starts with `request:`, means the branch point:

```
git merge-base HEAD <default branch ref>
```

**Then prove it before spawning anything:**

```
git rev-parse <fixed point>
git diff --stat <fixed point>
git status --short
```

The ref has to resolve, and there has to be something to review — **tracked changes or untracked files, either counts**.

If both come back empty, stop. There is no review to run:

```
– **review** nothing to review since <fixed point>
```

## 2. Find the spec

A `no-behaviour:` line skips this step — see the next section. Otherwise read [references/find-the-spec.md](references/find-the-spec.md) and follow it.

## No behaviour to review

If `$ARGUMENTS` carries a line beginning `no-behaviour:`, **spawn `devflow:reviewer` alone** — not `spec-reviewer`, not `security-reviewer`, not `hardcase`, not a project agent. Print one line:

```
– **review** no behaviour — reviewer reads the words alone
```

Give it the fixed point, the file list and a **200 word ceiling**, and one more line: nothing here runs, so read the words against the repo — every link and anchor still lands, no section other files point to is gone, and no claim names a feature that is not there or contradicts a skill or agent. A failing case is the link that lands nowhere, the feature nothing builds, or the line that says the opposite.

If the harness will not let you spawn it, read [references/no-agents.md](references/no-agents.md).

Either way, go to step 4 next. There, write `skipped — no behaviour` under **Challenged**, **Security**, **Right thing** and **Project review**, and against their lines in **Worst of each**.

**`no-behaviour:` is a line `submit` passes down, and never something `review` works out from the diff.** It carries the reason `build` gave at its own gate for writing no test, word for word.

**It is a third state, and it is not the other two.** `NOT RUN` is an axis that should have run and could not. `none` is an axis that ran and found nothing. `skipped — no behaviour` is an axis that was never owed a run, and `submit` reads it as nothing to fix.

## 3. Spawn the axes

Read [references/axes.md](references/axes.md) and follow it: `reviewer` always, `spec-reviewer` when step 2 found a spec, `security-reviewer` when the danger list says so, each agent a `- Review agent:` line in `CLAUDE.md` names, then `hardcase` against what they found — and how `Challenged` prints in step 4. If the harness will not let you spawn an agent, read [references/no-agents.md](references/no-agents.md).

## 4. Report both, blended into neither

```markdown
## Built right
<reviewer's report, or: NOT RUN — <why, in one line>>

## Challenged
<hardcase's report, or: nothing to challenge — the first axis was clean,
 or: NOT RUN — <why>, or: skipped — no behaviour>

## Security
<security-reviewer's report, or: skipped — no security item touched,
 or: NOT RUN — <why>, or: skipped — no behaviour>

## Right thing
<spec-reviewer's report, or: no spec available, axis skipped, or: NOT RUN — <why>,
 or: skipped — no behaviour>

## Project review
<each named agent's report, or: NOT RUN — <why>, or: skipped — no behaviour>

## Worst of each
- Built right: <the one finding that matters most, or none, or NOT RUN>
- Security: <the one finding that matters most, or none, or skipped — no security item touched, or NOT RUN, or skipped — no behaviour>
- Right thing: <the one finding that matters most, or none, or NOT RUN, or skipped — no behaviour>
- Project review: <the one finding that matters most, or none, or NOT RUN, or skipped — no behaviour>
```

**Do not merge the lists, and do not rank across them.** No single overall winner: one worst finding per axis, or none. With no `- Review agent:` line, leave out **Project review** and its line.

**Carry a `Not reported:` line through.** If either agent says findings were dropped, say so beside that axis — the same reason `NOT RUN` is not `none`.

## 5. Hand back

If `submit` called this, return the report and stop — `submit` decides what to fix. If a human called it, add one line on what you would do first. Do not fix anything here. This skill reads.

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never edit, stage, commit or push. `review` reads and reports.
- Never spawn an axis without proving the fixed point resolves first.
- Never invent a spec, and never treat a missing spec as a finding.
- Never merge the axes or rank one against another.
- Never report an axis as clean when it did not run. `none`, `NOT RUN` and `skipped — no behaviour` are three different answers.
- Never work `no behaviour` out from the diff. It is a line `submit` passed down, or it is not there.
- Never pass this session's reasoning into an agent's prompt.
- Never run an agent that no `- Review agent:` line names, and never look in `.claude/agents/` for one.
- Never start `security-reviewer` unless `reviewer`'s danger list line names one of the five security items.
- Never run `hardcase` against the spec axis, and never let it add a finding of its own.
- Never drop a finding because `hardcase` broke it. Print both and let `submit` decide.
