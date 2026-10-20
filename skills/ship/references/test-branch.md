# A Verify that reads the test site

`ship` step 2 reads this when `## Workflow` has a `- Test branch:` line.

`submit` merges each PR into the test branch a `- Test branch: <branch> <url>` line names
([test-branch.md](../../submit/references/test-branch.md)), so the test site already has this
change. A `Verify` line in `## Deploy` that holds that same link would pass while live was
never checked. That is the case after go-live, when `main` moved to the live domain and the
line was not changed. So when the branch is on GitHub (`git ls-remote --heads origin
<branch>` prints a line) and at least one `Verify` line, and every one, holds the test link itself — the same
link, or a path under it — stop before the merge. One `Verify` line that reads another site
already checks live, so a second line on the test site is fine:

```
✗ **live** Verify points at the test site — change it to the live link
```

Before go-live the branch is not on GitHub yet, `main` deploys to the test site, and the
`Verify` line is right as it is.
