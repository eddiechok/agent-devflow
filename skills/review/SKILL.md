---
name: review
description: "Use when a branch needs reviewing before it becomes a pull request, or when you want a read on work you did not write. Reviews everything between a fixed point and now along two axes, kept apart on purpose - is it built right, and is it the right thing. Each axis runs in a fresh agent that never sees this session's reasoning. Called by submit at step 5, and safe to start yourself on any branch."
argument-hint: "[fixed point - a branch, tag or SHA. Defaults to the branch point]"
allowed-tools: Bash(git rev-parse:*), Bash(git merge-base:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git symbolic-ref:*), Bash(gh issue view:*)
---

# review

Two axes, two fresh agents, no blending.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- Changed files: !`git status --short 2>/dev/null || true`

## 1. Pin the fixed point

`$ARGUMENTS` is the fixed point if given. Otherwise use the branch point:

```
git merge-base HEAD <default branch ref>
```

**Then prove it before spawning anything:**

```
git rev-parse <fixed point>
git diff --stat <fixed point>
git status --short
```

The ref has to resolve, and there has to be something to review — **tracked changes or untracked files, either counts**. A typo'd ref or an empty range fails here, in front of the human, rather than inside two agents that then review nothing and report nothing wrong.

If both come back empty, say so and stop. There is no review to run.

## 2. Find the spec

In this order, first hit wins:

1. **A plan file** — **list `.devflow/plans/`** and pick the one whose subject is this work. Deep work writes one. Do not match the filename against the branch name: a harness that names your branch for you, as Claude Code on the web does, makes that match fail on exactly the work that has a spec. If several are plausible, name them and ask.
2. **An issue** — a reference in the branch name or the commits since the fixed point, like `Closes #45`. Read it with `gh issue view`, or whatever GitHub access this environment has. If you cannot open it, there is no spec — say so and skip the axis. A spec you could not read is not a spec.
3. **Nothing.** That is a normal answer for a Quick fix.

**Never invent requirements.** No spec means the second axis does not run — not that you imagine what it would have said.

## 3. Spawn the axes

Both get the fixed point, the file list, and a **400 word ceiling**. Both run in parallel where you can, and neither is told what the other found.

- **`devflow:reviewer`** — always. Is it built right.
- **`devflow:spec-reviewer`** — only when step 2 found a spec. Is it the right thing. Pass it the spec's path or contents.

Fresh context is the whole point. Do not paste this session's reasoning, your plan, or your own account of what the change does into either prompt — that is the thing an independent reviewer would not have. Give them the range and let them read it.

### Then challenge the first axis

**`devflow:hardcase`** — a third agent, and the only one that runs second, because it
needs something to argue with. Give it the fixed point and `reviewer`'s findings, and
nothing else: not the spec, not `spec-reviewer`'s report, and not this session.

**Only when `reviewer` reported something.** A clean first axis has nothing to refute, so
say so in one line and skip it. This is the one place in the plugin where the expensive
step is skipped by default, and it is safe because it is skipped exactly when there is no
work for it.

**It challenges the first axis only.** `spec-reviewer`'s findings each quote the line of
the spec they rest on, so they are already anchored to something outside the reviewer's
judgement. `reviewer`'s are not — its bar is naming a failing case, and a plausible case
that cannot actually be reached passes that bar. That is the gap `hardcase` closes.

It does not get a vote. It reports which findings stand, which fall and why, and `submit`
decides. A challenge is one more thing on the table, not a verdict that removes one.

### When the harness will not let you spawn an agent

Some sessions forbid starting an agent unless the human asked for one, in the system prompt. **This is a plan restriction, not a web one** — it rides on Pro, and it fires locally exactly as it does on the web, so do not go looking for it by asking where you are running. Look at your own instructions: if something there says not to spawn an agent unless asked, this section applies, and otherwise it does not. Where it applies, neither axis can start on its own.

Getting this backwards costs in both directions. Assume it is a web rule and a Pro session working locally hits the block with no warning and no `NOT RUN` line. Assume every web session has it and a Max or Team session on the web stops to ask a question nothing was blocking, then labels a review `NOT RUN` that would have run.

Do not skip it quietly, and do not review the code yourself instead — this session wrote it, which is the thing the two agents exist to avoid. Say it in one line and ask:

```
This harness only starts agents when you ask. Say "run the review" and both axes go.
```

If that answer does not come, the axis **did not run**. Report it as `NOT RUN` in step 4 with the reason, and let `submit` carry it into the PR. An axis that did not run is not a clean axis.

## 4. Report both, blended into neither

```markdown
## Built right
<reviewer's report, or: NOT RUN — <why, in one line>>

## Challenged
<hardcase's report, or: nothing to challenge — the first axis was clean,
 or: NOT RUN — <why>>

## Right thing
<spec-reviewer's report, or: no spec available, axis skipped, or: NOT RUN — <why>>

## Worst of each
- Built right: <the one finding that matters most, or none, or NOT RUN>
- Right thing: <the one finding that matters most, or none, or NOT RUN>
```

**`Challenged` sits under `Built right` because it is about that axis, not beside it.**
It is not a third axis and it never appears in `Worst of each` — there is no worst
challenge. Print `hardcase`'s three sections as it wrote them, `Falls` first, and do not
delete a finding from `Built right` because it fell. Both readings go to `submit`
together; the point is that whoever decides can see the argument, not just its outcome.

**Do not merge the two lists, and do not rank across them.** A change can follow every rule in the repo while building the wrong thing, or build exactly the right thing in a way the repo forbids. One blended verdict lets the passing axis hide the failing one, which is the whole reason the axes are separate.

No single overall winner. One worst finding per axis, or none.

**Carry a `Not reported:` line through.** An axis that ran out of room is not an axis that found nothing, and `submit` decides what to fix from what you print. If either agent says findings were dropped, say so beside that axis — the same reason `NOT RUN` is not `none`.

## 5. Hand back

If `submit` called this, return the report and stop — `submit` decides what to fix.

If a human called it, add one line on what you would do first. Do not fix anything here. This skill reads.

## Rules

- Never edit, stage, commit or push. `review` reads and reports.
- Never spawn an axis without proving the fixed point resolves first.
- Never invent a spec, and never treat a missing spec as a finding.
- Never merge the two axes or rank one against the other.
- Never report an axis as clean when it did not run. `none` and `NOT RUN` are different answers.
- Never pass this session's reasoning into an agent's prompt.
- Never run `hardcase` against the spec axis, and never let it add a finding of its own.
- Never drop a finding because `hardcase` broke it. Print both and let `submit` decide.
