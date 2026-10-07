# Landing a worktree branch on main

For direct mode, when the session is in a **linked worktree**: its branch is not main, and
main is probably checked out in another folder. Used by `submit` (direct), multitask, plan
chains and sweep. Written once so none of them invent their own.

A worktree is linked when `git rev-parse --path-format=absolute --git-dir --git-common-dir`
prints two different paths. The main checkout is the folder that holds the common dir.

## The sequence

1. **Rebase on the default branch ref**, so the branch sits on top of whatever main is now:

   ```
   git rebase --rebase-merges <default branch ref>
   ```

   `--rebase-merges` keeps the `--no-ff` merge a plan chain leaves; a plain rebase flattens
   it. When main moved, the commits are replayed and their SHAs change; report the landed
   ones. With a remote, `git fetch origin` first. A conflict is not yours to guess at: stop
   and say which files.
2. **Run the checks again**, bare, one per call. They must postdate the rebase.
3. **Land it.** With a remote:

   ```
   git push origin HEAD:<default>
   ```

   With no remote, from the main checkout. `--ff-only` moves whatever that folder has
   checked out, so first make sure it is the default branch:

   ```
   git -C <main checkout> symbolic-ref --short -q HEAD
   ```

   Anything but `<default>` — another branch, or nothing at all for a detached `HEAD` —
   and stop, changing nothing:

   ```
   ✗ **landed** main folder is on <what it printed, or detached>
   switch it to <default>, then run submit again
   ```

   On the default branch:

   ```
   git -C <main checkout> merge --ff-only <branch>
   ```

Both refuse and change nothing if main moved since step 1, and `--ff-only` also aborts
without touching a thing when the main checkout has uncommitted changes to the same files.
When it refuses, rebase again **once**, run the checks again, and land again. Refused a
second time, stop. Nothing changed, and the branch still holds the work:

```
✗ **landed** main moved twice — run submit again to land it
```

On success:

```
✓ **landed** <branch> on main, <sha>
```

## Never

- Never `git update-ref refs/heads/<default> ...`. It is not refused, and it leaves the main
  checkout's index and working tree stale: the landed files show there as staged deletions,
  and the next commit in that folder reverts the work.
- Never `git push . HEAD:main`. It is refused while main is checked out in another worktree.
- Never `git fetch . HEAD:main`. Refused for the same reason.
- Never force a push, and never merge main into the branch to dodge the rebase.

## After landing

The branch may go, only with the safe form, which refuses a branch that is not merged:

```
git branch -d <branch>
```

Never `-D`. The worktree is not removed from here: the harness that made it clears it.
