# Landing a worktree branch on main

For direct mode, when the session is in a **linked worktree**: its branch is not main, and
main is probably checked out in another folder. Used by `submit` (direct), multitask, plan
chains and sweep. Written once so none of them invent their own.

A worktree is linked when `git rev-parse --path-format=absolute --git-dir --git-common-dir`
prints two different paths. The main checkout is the folder that holds the common dir.

**A pinned branch lands here too.** A cloud session (Claude Code on the web:
`[ "$CLAUDE_CODE_REMOTE" = "true" ]`) is no linked worktree, as the two paths agree, but its
harness pins a branch that is not the default (`claude/...`) and the session may not leave
it. Its pull and push would reach that branch, never main. So it follows this file as a
worktree does: it always has a remote, so step 3 is the push. Never merge main into it to
get there.

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

**A pinned branch's push refused for permission** is not main moving: the remote answers
`403`, `permission denied` or a branch-protection message, never `rejected (fetch first)`.
Rebasing again cannot help, so do not. Keep the work, because a cloud container does not
outlive the session: push the pinned branch itself, then stop.

```
git push origin HEAD
```

An earlier refused run may have pushed this branch already, and step 1's rebase rewrote
those commits, so that push is refused as not a fast-forward. Then, and only then, push it
with a lease. `--force-if-includes` is what makes it refuse when anyone else pushed there:
step 1's fetch already moved `origin/<branch>`, so the lease alone would not.

```
git push --force-with-lease --force-if-includes origin HEAD
```

```
✗ **landed** <default> refused the push — work kept on <branch>
```

On the next lines, tell the human how to land it from a machine that may push, this file's
steps by hand: `git fetch origin`, `git switch --detach origin/<branch>`,
`git rebase --rebase-merges origin/<default>`, run the project's checks, then `git push origin HEAD:<default>`.

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
- Never force a push, and never merge main into the branch to dodge the rebase. The one
  exception is above: `--force-with-lease --force-if-includes` on a pinned branch's own ref, after its push to
  the default branch was refused. Never on the default branch.

## After landing

The branch may go, only with the safe form, which refuses a branch that is not merged:

```
git branch -d <branch>
```

Never `-D`. The worktree is not removed from here: the harness that made it clears it.
