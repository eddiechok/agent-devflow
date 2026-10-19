# agent-devflow

## Checks

Each Test line runs alone; there is no wrapper for them all.

- Test: python3 hooks/test-bash-guard.py
- Test: python3 hooks/test-secret-guard.py
- Test: python3 skills/test-frontmatter.py
- Test: python3 skills/lesson-review/test-count-waste.py
- Test: python3 evals/test-run.py
- Test: python3 scripts/test-validate-plugin.py
- Lint: python3 scripts/validate-plugin.py

`python3 evals/run.py` drives real Claude sessions and costs money: never a check.
No typecheck: nothing here is typed.

## Deploy
- Deploy: cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")" && claude plugin update devflow@eddiechok-devflow --scope local
- Verify: python3 -c 'import json,os,sys; d=json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json"))); sys.exit(0 if any(e.get("projectPath")==sys.argv[1] and e.get("gitCommitSha")==sys.argv[2] for e in d["plugins"]["devflow@eddiechok-devflow"]) else 1)' "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")" "$(git rev-parse origin/main)"
- Wait: 10s

Restart the session after a deploy.
A local-scope install is one entry per folder, so Deploy runs in the main checkout.

## Plans
- Tracker: github

## Workflow
- Mode: pr
- About: devflow: one dev loop for features, changes, bug fixes and chores — sizes the work, writes the test first, proves the code runs, opens a PR.
