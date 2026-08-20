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
