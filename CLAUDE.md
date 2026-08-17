# agent-devflow

## Checks

No package manager here — the checks are scripts and the plugin CLI. Two test
commands, deliberately: there is no wrapper that runs both, and adding one would
be changing the project to suit the tool.

- Test: python3 hooks/test-bash-guard.py
- Test: python3 skills/test-frontmatter.py
- Lint: claude plugin validate .

`claude plugin validate .` exits 0 with **exactly one warning**, about the missing
`version` field. That warning is intentional — with no version, `/plugin update`
picks up every push — so it is a pass, not a failure. A second warning means
something is genuinely wrong. Do not add `--strict`; it turns the intentional
warning into an error.

There is no typecheck: nothing here is a typed language.
