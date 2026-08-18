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

1. **A plan file** — `.devflow/plans/<name>.md` matching the branch or the work. Deep work writes one.
2. **An issue** — a reference in the branch name or the commits since the fixed point, like `Closes #45`. Read it with `gh issue view`.
3. **Nothing.** That is a normal answer for a Quick fix.

**Never invent requirements.** No spec means the second axis does not run — not that you imagine what it would have said.

## 3. Spawn the axes

Both get the fixed point, the file list, and a **400 word ceiling**. Both run in parallel where you can, and neither is told what the other found.

- **`devflow:reviewer`** — always. Is it built right.
- **`devflow:spec-reviewer`** — only when step 2 found a spec. Is it the right thing. Pass it the spec's path or contents.

Fresh context is the whole point. Do not paste this session's reasoning, your plan, or your own account of what the change does into either prompt — that is the thing an independent reviewer would not have. Give them the range and let them read it.

## 4. Report both, blended into neither

```markdown
## Built right
<reviewer's report>

## Right thing
<spec-reviewer's report, or: no spec available, axis skipped>

## Worst of each
- Built right: <the one finding that matters most, or none>
- Right thing: <the one finding that matters most, or none>
```

**Do not merge the two lists, and do not rank across them.** A change can follow every rule in the repo while building the wrong thing, or build exactly the right thing in a way the repo forbids. One blended verdict lets the passing axis hide the failing one, which is the whole reason the axes are separate.

No single overall winner. One worst finding per axis, or none.

## 5. Hand back

If `submit` called this, return the report and stop — `submit` decides what to fix.

If a human called it, add one line on what you would do first. Do not fix anything here. This skill reads.

## Rules

- Never edit, stage, commit or push. `review` reads and reports.
- Never spawn an axis without proving the fixed point resolves first.
- Never invent a spec, and never treat a missing spec as a finding.
- Never merge the two axes or rank one against the other.
- Never pass this session's reasoning into an agent's prompt.
