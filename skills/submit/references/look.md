# One short look at an edit no review has read

`submit` step 7 reads this when a file changed since the last review that read it.

**If any file changed since the last review that read it, one short look first.** Round 2 counts as a read of the lines it was scoped to. `devflow:reviewer` only, scoped to the lines that changed, a **200 word ceiling**, and no `hardcase`. Then step 5's last security read, before the commit.

**If the look finds something new, it gets at most 3 bounded fixes, one per look.** Two conditions on each fix, and both have to hold:

- **Small** — a few lines, the kind of fix that takes a minute.
- **In a file already changed on this branch.**

Both hold → fix it, run the `## Checks` block again — bare, one per call, as at step 2 — then **look again**, scoped to only the lines that fix changed, same agent, same ceiling. Hand that look a finding that fix did not cover too — a look can find two things — so the next fix takes it, or Known issues does once the cap is spent. Either fails — a bigger fix, or a file the branch did not touch — → **stop editing**, and put it under **Known issues** with every finding still waiting for a fix. Print what each look did, one line each:

```
✓ **look** fixed in place — skills/ship/SKILL.md, 2 lines
```

```
– **look** known issue — docs/pipeline.md, not on this branch
```

```
✓ **look** clean — the fix to skills/ship/SKILL.md reads right
```

**The last look only reports.** After the third fix, the look that reads it cannot fix anything: what it finds goes under **Known issues**, and a leftover bug is parked below. So the run always ends on a read, never on an edit. The loop stays bounded: review, round 2, look, at most 3 small fixes each read by its own look, done.
