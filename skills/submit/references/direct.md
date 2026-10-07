# submit in direct mode

`direct` means the work is committed on main and pushed, with no branch and no pull
request. Read this when `Mode: direct` is in the project's `## Workflow` block in
`CLAUDE.md` and no `mode: pr` line was handed to you. With a `mode: pr` line, `submit` is
exactly as written in its SKILL.md and this file is not read.

`flow` hands you two lines beside `request:` and any `tracker:` lines: `start: <sha>`, where
the work began, and `size: <Quick|Standard|Deep>`. Invoked directly with no `start:`, the
work was started by hand and the review's fixed point is found as step 5 says. With no
`size:`, treat the work as Standard.

## Step 1 — main is allowed

Do not stop on the default branch, and do not cut a branch. A session in a linked worktree
stays on that worktree's own branch. Print, unless `build` printed one this run:

```
✓ **branch** main — direct mode
```

Steps 2, 3, 4 and 6 run as written: the checks fresh, the debug sweep, the live check, and
the stale docs.

## Step 5 — review by size

Review follows the size `flow` gave, not the branch:

- **Quick** — no review. Print:

  ```
  – **review** skipped — Quick, direct mode
  ```

  Under Evidence in the Done report write `Review: skipped — Quick, direct mode`.
- **Standard and Deep** — `devflow:review`, as step 5 says, with one change: the fixed point
  is `start:`, not `git merge-base HEAD <default branch ref>`. On main the merge-base is
  `HEAD` itself and leaves nothing to review. Pass the request and any `no-behaviour:` line
  as usual, and act on what comes back the same way.

  **With no `start:` line**, nothing recorded where the work began, and `HEAD` would leave
  every commit already made on main unseen. The fixed point is the upstream, so every
  commit not yet pushed is reviewed along with what is uncommitted:

  ```
  git rev-parse @{upstream}
  ```

  **With no upstream** (the command fails: no remote, or the branch tracks nothing) fall
  back to `HEAD`, and print one line, because the review then reads only what is
  uncommitted:

  ```
  – **review** no upstream — only uncommitted work is reviewed
  ```

## Step 7 — commit on main, then push

The commit is conventional, as step 7 says. With no pull request to carry the Assumptions,
they go **in the commit message body**, one bullet each, under an `Assumptions:` line; leave
the line out when there were none. A `tracker:` action that closes an issue puts
`Closes #<n>` in the body too.

Then, with the checks green:

```
git pull --rebase
git push
```

Run each bare, one per call. A rebase that conflicts is not yours to guess at: stop and say
which files. After the push print `✓ **pushed** main, <sha>`.

**In a linked worktree** the branch is not main, so none of that applies. Commit on the
worktree's own branch, then land it as [land-on-main.md](land-on-main.md) says, which prints
its own `landed` line in place of `pushed`.

**No remote** (`git remote` prints nothing): commit only, never push, and say so in one line:

```
– **pushed** no remote — committed on main only
```

## Step 8 — no PR

Skip step 8: there is no body file, no `gh api` call and no PR link. What step 8's body
carries goes in the **Done report** in the chat instead: What, Why, Assumptions, How to
check this yourself, and Evidence, in the same shape. The report's last line is the pushed
commit, not a link.
