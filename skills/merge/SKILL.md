---
name: merge
description: "Use after submit, when the pull request is open and you want it merged but not deployed yet - so several PRs can go out in one deploy. Merges the PR the way ship does, cleans up its branch, and stops: no deploy, no live check. Run /devflow:ship on the merged PRs afterwards. Only a human can start it."
argument-hint: "[PR number, or blank for the current branch]"
allowed-tools: Bash(git status:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(gh pr view:*), ExitWorktree
disable-model-invocation: true
---

# merge

Merge it, clean up behind it, and stop. The deploy waits for `/devflow:ship`.

Why these rules are what they are: [docs/merge.md](../../docs/merge.md). Read it only if a
rule looks wrong.

## Read ship first

Read [../ship/SKILL.md](../ship/SKILL.md) and follow it, so the two cannot drift apart. This
skill is only what is different:

- Follow ship's Context, The boundary, and steps 1, 2 (including the conflict handover to
  `tend`, one attempt), 3 and 6. The handover is in
  [conflict-handover.md](../ship/references/conflict-handover.md).
- Skip step 4, the deploy, and step 5, the live check. Skip step 7 too: the report below
  replaces it.
- In step 2, the status line ends `✓ **merge** <method>`, with nothing after it about
  watching a deploy.

## Direct mode

With `Mode: direct` in the project's `## Workflow` block, no `mode: pr` line, and no PR
number in `$ARGUMENTS`, the work is already on main and there is nothing to merge. Print
`– **merge** direct mode, nothing to merge` and stop.

## Read the Deploy block before step 3

Look for a `## Deploy` block in the project's `CLAUDE.md`. It decides whether this merge
may happen at all, and what to say after it. Three cases:

- **A block with no `Deploy:` line.** CI deploys when the default branch moves, so a merge
  here starts the deploy. Stop and merge nothing:

  ```
  ✗ **merge** a merge here starts the deploy — run /devflow:ship <n> <n> when all are ready
  ```

- **No block at all.** Nothing says whether a merge starts a deploy. Merge, and print:

  ```
  – **deploy** no Deploy block — a merge may start one; /devflow:ship checks it live
  ```

- **A `Deploy:` line.** Merge, and print the line below. Do not run the `Deploy:` line:

  ```
  – **deploy** not run — /devflow:ship <n> <n> deploys them together
  ```

## Report

One shaped line per fact, then the next step. Name the PR that merged:

```
✓ **merged** #2 (squash), remote branch deleted

✓ **tended** #2 conflicted with main — tend resolved it (omit if none)

✓ **retargeted** #4 onto main, still open (omit if none)

– **deploy** not run — /devflow:ship 2 <n> deploys them together

✓ **cleaned** local branch, 3 screenshots in /tmp

→ **next** /devflow:ship <n> [<n>...]
```

The `deploy` line is the one the Deploy block chose above. The `next` line names the PR
just merged, plus any others the human has merged and not yet shipped.

## Rules

- Never run without a human starting it. `disable-model-invocation: true` stays, and so
  does the rule in `flow`, `submit` and the other skills not to call this.
- Never run a `Deploy` line. It is `/devflow:ship`'s.
- Never run a live check. Not even to see whether a merge started a deploy.
- Never merge where the block has no `Deploy:` line: that merge starts the deploy.
- Every rule in ship's Rules about refusing a PR, the merge method, a refused merge and a
  branch delete holds here as written.
