# A request that names a backlog file

**A path under `.devflow/backlog/` is not free text — it is a feature this project already
decided to build later.** First ask whether it was built already. A chip run started
before this file reached the default branch could not see it, so its commit and its PR
body name the file instead, on a `Backlog:` line. Look on the default branch, then, if
that finds nothing and `gh` answers, in the merged pull requests:

```
git log <default branch ref> --fixed-strings --grep="Backlog: .devflow/backlog/<name>.md" --format=%h -1
```

```
gh api 'search/issues?q=repo:{owner}/{repo}+is:pr+is:merged+in:body+%22Backlog:+.devflow/backlog/<name>.md%22' --jq '.items[] | select(.body | contains("Backlog: .devflow/backlog/<name>.md")) | .number'
```

The query sits in the path because `gh` fills `{owner}/{repo}` there and never in a `-f`
value. Keep the `--jq` filter. GitHub's phrase search is loose and matches bodies without the
line; only a number the filter prints is a hit.

**A hit means the feature shipped.** Remove the file, say so, and build nothing else: the
deletion is the whole change, so size it Quick and carry on to `build` and `submit`.

```
– **backlog** .devflow/backlog/<name>.md already built in <sha or #n>
deleting it, nothing else to build
```

**No hit** — read the file; its contents are the request, exactly as an issue body is.
Then remove the file and say so, so the deletion ships in this run's own PR rather than
lingering as a stale entry the next run reads and parks all over again:

```
rm .devflow/backlog/<name>.md
```

```
✓ **backlog** took .devflow/backlog/<name>.md — the file is deleted in this branch
```

**A request that ends `Also parked as .devflow/backlog/<name>.md`** came from a step 1b
chip. The text above that line is what to build, but keep that line in the request you
hand `submit` at step 5 — it is how `submit` knows to write the `Backlog:` line. If the
file is in this checkout, remove it and print the `took` line. If it is not, the kept run
has not merged yet; print this, and `submit` writes the `Backlog:` line a later run looks
for:

```
– **backlog** .devflow/backlog/<name>.md is not in this checkout
the commit names it, so a later run skips it
```
