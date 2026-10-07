# ship in direct mode

`direct` means the work is committed on main and pushed, with no branch and no pull
request. Read this when `Mode: direct` is in the project's `## Workflow` block in
`CLAUDE.md`, `$ARGUMENTS` holds no PR number, and no `mode: pr` line was given. Otherwise
`ship` is exactly as written in its SKILL.md and this file is not read.

There is no PR to merge for the work this session did, so `gh pr merge` never runs, no
branch is deleted and nothing is retargeted. What is left of `ship` is the deploy and the
live check, on the commit that was pushed.

## What replaces steps 1 to 3

1. **Find the commit.** It is `HEAD` on the default branch. In a linked worktree, or on
   any other branch, there is nothing pushed to main from here: say so and stop, because
   the branch is landed by `submit` through its land-on-main reference, not by this skill.
2. **Be sure it is pushed.** Run `git fetch origin`, then compare `git rev-parse HEAD` with
   `git rev-parse <default branch ref>`. They must match. A commit that is not pushed is
   not on the remote and nobody can deploy it from there:

   ```
   ✗ **deploy** HEAD is not pushed — push first, then run ship again
   ```

   With no remote (`git remote` prints nothing) there is no push to wait for: deploy the
   local `HEAD`, and say so in one line.
3. **Nothing to refuse.** There is no PR state, no review decision and no conflict to hand
   to `tend`. Checks still matter: if `gh` shows a red CI run for the commit, stop and name
   `tend`, which reads it as a red commit on main.

Print, then go to step 4:

```
✓ **commit** <short sha> on main — no PR to merge
```

## Steps 4 and 5, as written

Step 4 deploys and step 5 checks it is live, exactly as written, with the pushed commit in
the place of the merged one: the `## Deploy` block runs in order, `Verify` has to pass, and
the checkout it deploys must be at that commit holding nothing else. Step 6 deletes the
head branch of a merged PR; there is none, so skip it. Step 7's report drops the `merge`
and `branch` lines and keeps `deploy` and `live`.

## Someone else's PR

A PR number in `$ARGUMENTS`, or a PR from somebody else, still goes the PR path in
SKILL.md, merge and all. `direct` describes how this project's own work lands, not how a
contributor's does.
