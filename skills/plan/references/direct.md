# plan in direct mode

`direct` means the work lands on main, with no branch and no pull request. Read this when
`Mode:` in the project's `## Workflow` block of `CLAUDE.md` is `direct` and `flow` handed no
`mode: pr` line. With a `mode: pr` line, `plan` is exactly as its SKILL.md writes it and
this file is not read.

The chains are unchanged. They still run in worktrees, each built by its own
`devflow:builder`, at the same time, and `worktree.baseRef` is still written before the
first spawn. What changes is where this session stands, and where the chain branches go.

## No feature branch

Skip "Stand on the feature branch first": cut no feature branch, and never run
`git checkout -b`. Stand where the session already stands:

- **In the main folder**, on the default branch. The chains merge into main, here.
- **In a linked worktree** (`git rev-parse --path-format=absolute --git-dir
  --git-common-dir` prints two different paths). Stay on this worktree's own branch. The
  chains merge into it, and `submit` lands it on main afterwards through
  [land-on-main.md](../../submit/references/land-on-main.md), which `flow` calls once this
  skill reports back. Do not push from here.

The plan's `Branch:` line names the branch you stand on, as it always does: `main` in the
main folder, the worktree's own branch in a linked worktree. The base tag is cut from that
tip, and the base check at step 2 is unchanged.

## Merging the chains

Step 5 is as written, with one difference in what it merges into: the branch you stand on.
Check each chain with `git merge-tree --write-tree`, stop on a conflict, and then merge
with `git merge --no-ff <chain branch>`, in plan order. A merge commit is a commit on main,
so the history keeps one merge commit per chain, naming it, and the builders' own SHAs stay
as they reported them until `submit` pulls or rebases. If main moved meanwhile, that replays
them under new SHAs; the merge commits stay.

Steps 6 and 7, the cleanup and `chain: final`, are as written.

## Reporting back

Step 8 is as written, and `flow` calls `submit` from there. In the main folder `submit`
pushes main (`git pull --rebase=merges`, `git push`); with no remote it commits only, and says so
in one line. Nothing here pushes: a chain's commit is on main only once `submit` has
pushed it.
