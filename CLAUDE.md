# agent-devflow

## Checks

No package manager here — the checks are scripts and the plugin CLI. Three test
commands, deliberately: there is no wrapper that runs all of them, and adding one
would be changing the project to suit the tool.

- Test: python3 hooks/test-bash-guard.py
- Test: python3 skills/test-frontmatter.py
- Test: python3 evals/test-run.py
- Lint: claude plugin validate .

`evals/test-run.py` is the contract test for the eval runner's parser and
graders. It calls no model and costs nothing. **Running the evals themselves is
not a check** — `python3 evals/run.py` drives real Claude sessions and costs real
money, so it stays out of this block and gets run deliberately.

`claude plugin validate .` exits 0 with **exactly one warning**, about the missing
`version` field. That warning is intentional — with no version, `/plugin update`
picks up every push — so it is a pass, not a failure. A second warning means
something is genuinely wrong. Do not add `--strict`; it turns the intentional
warning into an error.

There is no typecheck: nothing here is a typed language.

## Deploy
- Deploy: cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")" && claude plugin update devflow@eddiechok-devflow --scope local
- Verify: python3 -c 'import json,os,sys; d=json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json"))); sys.exit(0 if any(e.get("projectPath")==sys.argv[1] and e.get("gitCommitSha")==sys.argv[2] for e in d["plugins"]["devflow@eddiechok-devflow"]) else 1)' "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")" "$(git rev-parse origin/main)"
- Wait: 10s

A merge to `main` changes nothing a session sees. The plugin is installed at
local scope from the main checkout, and the update copies it into a cache
directory named after the commit. Restart the session after it.

A local-scope install is one entry per folder, keyed to the folder the update
runs in. Run from a worktree, the update changes only that worktree's entry and
still says it updated, so the Deploy line goes to the main checkout first.
Verify reads the main checkout's entry for the merged commit. The cache
directory is no proof: it exists as soon as any folder updates.

## Plans
- Tracker: github
