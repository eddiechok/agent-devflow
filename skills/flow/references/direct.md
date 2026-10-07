# flow in direct mode

`direct` means commit straight on main, no branch, no pull request. `pr` is the way this
skill is written everywhere else. Read this when `Mode: direct` is in the project's
`## Workflow` block, and only then. The block's shape is in
[the setup skill](../../setup/SKILL.md).

## Read the mode

`Mode:` comes from `## Workflow` in the project's `CLAUDE.md`. Read it yourself; nothing
else carries it. No block means "not set up", and the step before step 0 has already called
`devflow:setup` for that.

## The override: one run in `pr`

A request that carries `--pr`, or says "PR this time" or words like it, is `pr` for this one
run, whatever the block says. Print it, then follow `flow` as written without this file:

```
✓ **override** pr for this run — Mode: direct in CLAUDE.md
```

Hand `mode: pr` on as its own line, on its own, to `build`, to `devflow:plan` and to
`devflow:submit`. Each reads `Mode:` from `CLAUDE.md` for itself, and the line is the only
thing that tells it this run is the exception. The block is never rewritten for it.

## What direct skips

- **Step 0's PR lookup.** There is no pull request to find. Skip the `Commits ahead` check
  and the `gh api` call, and do not print the `pr` line.
- **Step 0c, the fresh branch and the worktree.** Nothing is cut and no worktree is taken
  for the folder's sake. A session already in a linked worktree (`git-dir` differs from
  `git-common-dir`) works on that worktree's own branch, and `submit` lands it on main. A
  session in the main folder works on main. Do not tell `build` this is new work needing a
  fresh branch; tell it this is direct mode.

Everything else, sizing, the danger list, the rounds of questions, the wait for go and the
plan, runs as written.

```
✓ **branch** main — direct mode, no branch cut
```

## The start sha

Before the first edit, once the human has said go on Standard and Deep, record where the work
begins:

```
git rev-parse HEAD
```

Keep it as `start: <sha>`. It is the fixed point `review` judges the diff against, because on
main the usual merge-base with the default branch is `HEAD` itself and leaves nothing to
review. Record it once per run, never again after an edit.

## Step 5 in direct

`devflow:submit` is still called, in the same turn. Hand it, beside `request:` and any
`tracker:` lines:

```
start: <sha>
size: <Quick|Standard|Deep>
```

`size:` is what `submit` decides review by. Add `mode: pr` as its own line only when the
override above is in force.
