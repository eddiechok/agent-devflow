# Find the spec

`review` step 2 reads this, on every run without a `no-behaviour:` line.

In this order, first hit wins:

0. **A plan issue** — only if the project's `CLAUDE.md` has a `## Plans` block saying `github`. List them: `gh api 'repos/{owner}/{repo}/issues?labels=devflow:plan&state=open' --jq '.[] | select(.pull_request | not) | {number, title}'`, or whatever GitHub access this environment has. If `gh` cannot fill `{owner}/{repo}` from the git remote, write the owner and repo in yourself. With no `gh` installed, list them with `curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN" "https://api.github.com/repos/<owner>/<repo>/issues?labels=devflow:plan&state=open"`, reading `<owner>/<repo>` from `git remote get-url origin`, and skip entries with a `pull_request` key. If the remote does not name a GitHub repo, write them in yourself. Never print `$GH_TOKEN`, and send it to `api.github.com` and no other host. Pick the one whose subject is this work and read its body — `gh api repos/{owner}/{repo}/issues/<n> --jq .body` — it has the shape of a plan file. If `gh` cannot answer, say so and go on to the file — the same job may have fallen back to one.
1. **A plan file** — **list `.devflow/plans/`** and pick the one whose subject is this work. Deep work writes one. Do not match the filename against the branch name. If several are plausible, name them and ask.
2. **An issue** — a reference in the branch name or the commits since the fixed point, like `Closes #45`. Read it with `gh api repos/{owner}/{repo}/issues/<n> --jq .body` — with no `gh`, the same `curl` call on `https://api.github.com/repos/<owner>/<repo>/issues/<n>` — or whatever GitHub access this environment has. If you cannot open it, say so and go on to the next item.
3. **The request itself** — the text after `request:` in `$ARGUMENTS`, if any. Pass it to `spec-reviewer` as pasted contents, and say in the report that the spec was the request.
4. **Nothing.**

**Never invent requirements.** No spec means the second axis does not run — not that you imagine what it would have said.
