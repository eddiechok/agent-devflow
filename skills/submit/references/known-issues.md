# Sort Known issues, and park the leftover bugs

`submit` step 7 reads this before the commit, when anything is going under **Known issues**.

**Then sort what is going under Known issues.** Each item is one of three kinds:

- **A rejected finding** — a finding you checked and refused, with its reason.
- **A test gap** — something this run could not prove: no live check, no eval case, an axis `NOT RUN`, a review cut short.
- **A leftover bug** — a real flaw nobody fixed: a finding still standing after 2 rounds, something a look found that was too big, outside the branch, or found by the last look, or a bug that was already there and turned up in passing.

**Only a leftover bug is parked.** The other two are notes for whoever merges, and they stay in the PR body alone. A leftover bug is work, and a merged PR body is where work goes to be forgotten. **Park them before the commit**, so a backlog file ships in this PR. Park each one the way `flow` step 1b parks a feature — look for a `## Plans` block in `CLAUDE.md`.

**Never park the same bug twice.** An earlier run on this branch may have parked it and then stopped before a PR body could link it. So first list what is already parked — the open issues, through the `curl` form in `flow`'s `references/curl-fallback.md` when there is no `gh`, and the files under `.devflow/backlog/`:

```
gh api --paginate 'repos/{owner}/{repo}/issues?labels=devflow:backlog&state=open' --jq '.[] | select(.pull_request | not) | {number, title, body}'
```

Read every page: a bug parked from another branch is likely an old one. With `curl`, add `&per_page=100&page=<n>` and read until a page comes back short.

One whose body names this bug is already its link, whichever branch its `Found on:` line names — most likely `Found on: <this branch>`, but a bug that was already there may have been parked from another. Use it, and file nothing.

**`## Plans` says `github`:** make the label if it is missing ("already exists" is fine), then file one issue per leftover bug. With no `gh`, use the `curl` form in `flow`'s `references/curl-fallback.md` for both.

```
gh label create devflow:backlog --description "A devflow parked feature" --color 5319E7
```

```
gh api repos/{owner}/{repo}/issues -f title="<the bug>" -F body=@<body file> -f 'labels[]=devflow:backlog' --jq .number
```

Write each body to a fresh file outside the repo — never a fixed path, which another session can reach first:

```
mktemp "${TMPDIR:-/tmp}/devflow-backlog.XXXXXX"
```

The path it prints is `<body file>`. The body says what is wrong, where, and the fix if you know it, plus one line `Found on: <this branch>`. Remove the file after its issue is filed.

**No block, `local`, or a `gh` failure:** write `.devflow/backlog/<short-name>.md` instead, the same shape, under a name `flow`'s `references/split-and-park.md` name check allows. It is committed with the rest of the branch.

The bug's Known issues line then ends with where it went — `— parked as #48`, or `— parked as .devflow/backlog/<short-name>.md`. **On an update, a bug the PR body already links is not parked again**; it keeps its link. One that has been fixed since is step 7's, in `SKILL.md`.

**A backlog file is an edit**, written or deleted, and step 7's checks ran before it: run the `## Checks` block again — bare, one per call — before the commit.

Print one line when anything was parked:

```
✓ **parked** #48 look found stale docs/pipeline.md, not on this branch
```

```
✗ **parked** github asked, wrote .devflow/backlog/<name>.md — gh said <the error>
```
