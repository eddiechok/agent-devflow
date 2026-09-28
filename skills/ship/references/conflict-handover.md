# The conflict is yours to hand over

**`mergeable` is `CONFLICTING`, and that is the only thing this PR is reporting** — print
this, then run `devflow:tend` for this PR:

```
✗ **conflict** handing #32 to tend, then re-reading the state
```

**A PR reporting two things at once is not a conflict to hand over.** Conflicting *and* a
red check, conflicting *and* changes requested — `tend` would work the whole list, so what
started as resolving a merge ends with a reviewer answered by a skill the human started to
merge something. **Read all four conditions before you act on any of them**, and when more
than one is true, take the stop below and name every one of them.

A conflict is not the branch being wrong. It is what happens when another pull request
merges first, and the fix is mechanical: `tend` merges the default branch in, reads both
sides, and re-submits — so `review`'s two agents, which never saw this session, read the
resolution before it comes back here.

**When it returns, run step 2 again from the top** — the same `gh pr view`, and **all four
conditions, not just `mergeable`.** `tend` pushed, so two things changed that the first
read cannot tell you: CI started over, and the mergeability GitHub computed a minute ago
is stale. A PR that arrives back here green on the one field you looked at is not a PR
that is ready.

- **`MERGEABLE`, checks finished and passing, nothing else reported** → step 3, and merge.
- **A check running again** → that is step 2's ordinary stop, and it is the common case
  right after a push. Stop and say the checks are running, exactly as you would have
  before the handoff. Do not wait it out, and do not merge past it.
- **`mergeable` is `UNKNOWN`** → GitHub computes it asynchronously and answers `UNKNOWN`
  for the first seconds after any push, which is precisely when this read lands. It is not
  a yes. Wait, read once more, and go on **only if it comes back `MERGEABLE` and the
  checks have finished** — mergeability resolves in seconds and CI takes minutes, so a
  second read that says `MERGEABLE` says nothing at all about the checks. Anything else,
  stop. Never treat "not `CONFLICTING`" as clear.
- **Still `CONFLICTING`** → **stop, and hand it to the human.** **One attempt, and never a
  second.** A conflict `tend` could not settle is one more `tend` will not settle either,
  and looping here rewrites somebody's branch over and over with nothing to show.
