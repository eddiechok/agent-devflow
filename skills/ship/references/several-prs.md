# ship with several PRs

Read this when `$ARGUMENTS` holds more than one PR number, such as
`/devflow:ship 155 156 157`. With one number or none, `ship` is exactly as written in its
SKILL.md and this file is not read.

A `Deploy` line deploys the main checkout at the merged commit, so one deploy ships every PR
merged before it. This path merges them all, deploys once, and checks each PR's own change.
The steps are the ones in SKILL.md; this file only says how they repeat.

## Check all, then merge any

Run steps 1 and 2 for every PR before merging any of them. Step 1 reads each PR's base and
what is stacked on it; step 2 reads its state. A PR is not ready, and the whole batch stops,
when it is:

- not `OPEN` and not `MERGED`
- carrying a failed check, or an unfinished one
- `CHANGES_REQUESTED`
- stacked, with a base that is not the default branch

Merge none of them. Name the first PR that is not ready and why, and stop. The human fixes
it and runs the same command again; nothing was merged, so nothing is left half done. Do not
merge the ready ones "so far": a batch that is half merged is a deploy that ships half of
what was asked for.

```
✗ **pr** #156 not ready, a check failed — none merged; run it again
```

## A conflict is handed over before anything merges

A `CONFLICTING` PR in the batch goes to `tend` as in step 2, before any PR is merged: read
[conflict-handover.md](conflict-handover.md). One attempt each. When `tend` comes back, the
step 2 conditions for that PR are read again whole, and a PR that is still not ready stops
the batch with nothing merged.

## An already-merged PR skips the merge, not the check

A PR that is already `MERGED` is not an error: it may have been merged by `/devflow:merge`,
which is how the batch got here. Run step 1 for it, since step 6 needs its head branch and
what is stacked on it. Skip steps 2 and 3 for it, and print:

```
– **merge** #n already merged
```

It still gets its live check in step 5, and its clean-up in step 6. If every PR in the batch
is already merged, there is nothing to merge and the deploy and checks still run.

## Merge the open ones in the order typed

For each open PR, in the order typed, run step 3. Before each one, read `mergeable` and
`mergeStateStatus` again: an earlier merge in this batch can make a later PR conflict, or
leave it `BEHIND` where the repo requires branches to be up to date, and the answer from the
check pass is stale by then.

That re-read lands seconds after the previous merge moved main, which is when GitHub
answers `UNKNOWN`. `UNKNOWN` is not a yes, in either field: read every 10 seconds for up to
2 minutes until both have an answer. Still `UNKNOWN` at the limit is a stop, as below.

A `BEHIND` PR is brought up to date by the forge, not by `tend`: there is nothing to
resolve. The update adds a merge commit, which rules out `--rebase` in step 3, and a repo
that requires linear history refuses `--merge` too: only a squash is sure to take it. So
read `squashMergeAllowed` with `gh repo view` before the update. Not allowed: stop, as
below. Allowed: write down its `headRefOid` and run
`gh api -X PUT repos/{owner}/{repo}/pulls/<n>/update-branch`. If update-branch fails (a fork
that refuses maintainer edits answers 403 or 422), stop, as below. The update runs after the
call returns, so read `headRefOid` every 10 seconds, for up to 2 minutes, until it differs
from the one written down: the checks before that are the old head's. A head that never
moves is a stop. Once it moves, print `✓ **pr** #n was behind main — branch updated`, wait
for the new head's checks, as [conflict-handover.md](conflict-handover.md) waits, and read
step 2 whole again. Step 3 then merges it with `--squash`, whatever its ladder would pick.

A PR that has become conflicting mid-batch goes to `tend` as in step 2, one attempt, and
step 2 is read whole again when it returns. Still not ready after that, or conflicting again:
stop where you are. The PRs merged so far stay merged, so say which they are, and which
were not, in the report.

## Deploy once, then check each PR

- Step 4 once, after the last merge. It deploys the checkout at the merged commit, which
  carries every PR.
- Step 5 for each PR: a first-hand check of that PR's own change, by the same test as step 5
  (would this have been true before the change?). One PR's check passing says nothing about
  another's. A `Verify` URL that serves one PR's change is not a check of the next.
- Step 6 for each PR: its head branch, its stacked PRs, its worktree branch. Step 6 retargets
  stacked PRs before it deletes a branch, for each PR in turn.

## The report

Step 7's report, once for the batch:

- one `merged` line per PR, or the `already merged` line
- one `deploy` line
- one `live` line per PR
- the `tended`, branch-updated and `retargeted` lines, one per PR they apply to
- one `cleaned` line for the batch

```
✓ **merged** #155 (squash), remote branch deleted

– **merge** #156 already merged

✓ **merged** #157 (squash), remote branch deleted

✓ **deploy** claude plugin update, ready in 48s

✓ **live** #155 the new rule is in the installed skill — confirmed

✓ **live** #156 the new rule is in the installed skill — confirmed

✗ **live** #157 the installed skill still has the old line
```
