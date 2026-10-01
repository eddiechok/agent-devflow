# Update the PR already open

`submit` step 8 reads this when the branch already has an open pull request.

**A PR already open** — push to the same branch, then **update that PR**. Never open a second one for a branch that has one, and report the number you updated rather than announcing a new one. Read the body that is there first — `gh api repos/{owner}/{repo}/pulls/<n> --jq .body` — then write the new one back:

```
gh api -X PATCH repos/{owner}/{repo}/pulls/<n> -F body=@<body file> --jq .html_url
```

What moves and what does not:

- **Evidence** — rewritten. It describes the checks *this* run made, not the ones the first run made.
- **Known issues** — worked out again from this run's review. Anything fixed since comes out.
- **What** and **Why** — extended if the change grew. Do not rewrite the original reason to match a follow-up.
- **Assumptions** — appended to, never replaced.

Then one line on what moved:

```
✓ **pr** updated #12 — 2 commits, evidence refreshed, 1 known issue cleared
```
