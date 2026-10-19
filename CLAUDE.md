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
- Deploy: sh scripts/deploy.sh
- Verify: python3 scripts/verify-deploy.py
- Wait: 10s

The deploy copies the main checkout, wherever it runs from.

## Plans
- Tracker: github

## Workflow
- Mode: pr
- About: devflow: one dev loop for features, changes, bug fixes and chores — sizes the work, writes the test first, proves the code runs, opens a PR.
