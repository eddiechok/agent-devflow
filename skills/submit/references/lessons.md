# A fact worth keeping is not always about devflow

`submit` step 6 reads this when the run learned something worth keeping.

Two kinds of lesson, and this run is the only one that can tell them apart — no subagent
does this sort, because a fresh agent was not there for the mistake.

**A fact about this project** — "the tests need the sandbox key", something the next run
on this repo would need and `CLAUDE.md` does not already say — gets **add one line for it
to the project's CLAUDE.md**, in this same commit, so the human approves it with the work
rather than discovering it cold on a later run. List it under **What** in the PR body too.
Print:

```
✓ **lesson** added to CLAUDE.md — the tests need the sandbox key
```

Nothing to add → print nothing. This is not step 6's `docs` line, and does not replace it.

**A fact about devflow itself** — `flow` sized something wrong, a review finding fell,
a deploy's `Verify` failed — never goes into `CLAUDE.md`. Call `devflow:lesson` instead;
`flow`, `review` and `ship` already call it on their own clear signs, so this is only for
one your own run noticed that none of them did.
