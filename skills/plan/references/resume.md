# Resuming a plan — the worked detail

`SKILL.md`'s "Resume it" section says the shape: read the plan, then read what exists, then
pick up "Run one builder per chain" with the chains that are not done. This is what each of
those checks looks like in full.

**A chain branch that exists and is not merged is a chain that was started.** Say so, and
pick that chain up at the merge step rather than rebuilding it — its pieces are already
committed on that branch, and a second builder at the same chain would build them twice.
`git branch --no-merged` names the ones still outstanding. A chain whose branch is gone
and whose pieces are in the log finished and merged already; leave it alone.

**But check its base first, before it goes anywhere near the merge step.** The loop tagged
this branch's tip before the chains were cut, `devflow/<plan short-name>/base`, exactly so
a resumed session can ask the same question the original one asked:

```
git merge-base --is-ancestor devflow/<plan short-name>/base <chain branch>
```

A non-zero exit means that chain was cut from the default branch — the run that started it
stopped for this very reason and told the human to restart. **Do not merge it, and do not
pick it up.** Print `✗ **chains** chain <letter> cut from the default branch —
rebuilding, kept <branch>`, then treat the chain as not started: it
goes back into the spawn loop, and its old branch and worktree stay on disk for the human
to delete. If the tag is missing, you cannot tell either way: print
`✗ **chains** base tag missing — cannot tell where <letter> was cut; merged nothing`,
and ask the human which it is.

**Then check it is whole.** A branch that descends from the tag can still be a chain that
stopped early — its builder said `stuck` on piece 2 of 3, and its worktree, not this tree,
holds the half-built piece. Read what the branch has:

```
git log devflow/<plan short-name>/base..<chain branch> --oneline
```

Every piece of that chain has a commit there, or the chain is not done. **All present** →
the merge step, as above. **Fewer** → merge what is there first, `merge-tree` check and
`--no-ff` as in the loop, because those pieces are finished commits; then send the chain
back into the spawn loop, and print `✗ **chains** chain <letter> stopped at piece <n>;
merging <list>, rebuild from <n>`. The builder reads the log and skips the pieces already in
it. If `git worktree list` still shows that chain's old worktree, the half-built piece is
inside it: say that too, leave the worktree for the human, and let the new builder start
that piece over. That is the one place resume loses work, and it says so rather than
pretending the half-piece was carried across.

**Then look at the `Status` line**, and at any worktree the list still shows. A dirty tree
on a resumed plan is a piece that was started and not committed — the session died, you
stopped it, or `build` gave up after three tries. It is not the next piece. It is that
chain's first unbuilt piece, part done.

**A `?? .devflow/plans/` line is not dirt, and neither is `?? .devflow/backlog/`:** the
plan file is untracked until `submit` commits it, and a backlog file parked this run is
untracked the same way until the run that keeps it commits it, so only *other* changed or
untracked files make the tree dirty.

```
Deep — resuming email-alerts, chain A merged, chain B started and not committed
```

Hand the builder **that chain**, and say the tree is dirty — it is the third input the
builder takes, and it passes it through to `build` for the first piece it picks up, which
keeps what is there and writes a test at the seam before touching it, its rule for code
that arrived without one. Never start a chain from scratch beside a half-built one, and
never clean the tree to make the resume simpler — that is the work, thrown away.

**A dirty tree here means that chain runs first, alone, and without a worktree.** The
uncommitted work is in *this* tree, and a worktree is cut from commits — it would not
carry a single uncommitted line across, so a builder spawned with `isolation: "worktree"`
and told `dirty` would find a clean checkout, rebuild the piece, and leave the real
half-piece behind for `submit` to stage beside it. So spawn that one chain **without**
`isolation` on the Agent call, on this branch, exactly as the sequential path does, and
wait for its report. Only then do the other chains go out in parallel. A dirty tree on a
resumed plan can only have come from the sequential path, so this is the one crossing
between the two paths, and it is handled by staying on the sequential one for one chain.
