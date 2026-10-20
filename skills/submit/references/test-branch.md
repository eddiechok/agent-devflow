# Merge into the test branch

`submit` step 8 reads this when `## Workflow` has a `- Test branch: <branch> <url>` line,
in pr mode. `- Test branch: none`, or no line, skips it. The PR still goes to the default
branch; the test branch is throw-away, there only so the human can check on the test site.

## When

Right after the push, before the PR is opened or updated, so the body can say what
happened. The branch must be on GitHub first; the push puts it there.

## Merge on GitHub

No checkout of the test branch is needed. GitHub merges it:

```
gh api -X POST repos/{owner}/{repo}/merges -f base=<test branch> -f head=<pr branch> -f commit_message="Merge <pr branch> into <test branch> for the test site"
```

Each answer has one route:

- **201** — merged. `✓ **testsite** merged into develop — test site updating`
- **204** — already there, nothing to merge. `– **testsite** develop already has it`
- **404** — the test branch is not on GitHub yet: a new project that still deploys `main` to
  its test site. `– **testsite** develop not on GitHub yet — skipped`, and the check
  steps are the local ones.
- **409** — a conflict. Fix it below.
- Anything else → `✗ **testsite** <code> from GitHub — test site not updated`, and the
  check steps are the local ones.

Do not wait for the test site to deploy. Its CI takes the time it takes; the PR link is
enough for the human to come back to.

## A conflict

Another branch on the test branch touched the same lines. **One try**, then stop.

1. Read `git config rerere.enabled`, bare. Not `true` → run
   `git config rerere.enabled true` and print `✓ **testsite** rerere on — a fix here is reused on main`.
   git records this fix, and reuses it when the same conflict comes back as the PR merges
   into the default branch.
2. `git fetch origin`, and check out the test branch in a temporary worktree:
   `git worktree add --detach <temp folder> origin/<test branch>`.
3. In that folder, `git merge origin/<pr branch>`. Fix the conflict by reading both sides,
   as `tend` does ([tend's conflicts](../../tend/SKILL.md#conflicts-and-a-stale-base-are-yours-too)).
   A side kept whole is said, with why, in the Done report.
4. Commit the merge, then start `devflow:reviewer` on the fix alone. `devflow:review` reads
   the session's folder, not this one, so give the agent the folder and the command that
   shows only what the fix changed against git's own conflicted merge:
   `git -C <temp folder> show --remerge-diff HEAD`. Act on what it finds, in that folder.
5. `git push origin HEAD:<test branch>` — a normal merge commit, never force-push. A push
   refused because the test branch moved is the one try used up.
6. Remove the temporary worktree.

Cannot fix it in one try → `✗ **testsite** conflict not fixed — test site not updated`.
Remove the temporary worktree, give the local check steps, and go on to the PR. The PR
to the default branch is still good; only the test site is behind.

**Never merge the test branch into the PR branch.** It holds other branches' untested work,
and the PR would carry it to the default branch.

## The check steps

When the merge landed — 201, 204, or a fixed conflict — **How to check this yourself** starts
with the test site, then the local steps:

```
Test site: <link from the Test branch line> (updates once its deploy finishes)
```

Otherwise the steps are the local ones alone, and the body names no test site link.
