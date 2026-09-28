# Parking the features step 1b did not keep

Once the kept feature is settled, park the others, one entry each, the same way
`devflow:plan` writes a plan — look for a `## Plans` block in `CLAUDE.md`.

**`## Plans` says `github`:** make the label if it is missing ("already exists" is fine),
then file one issue per parked feature. With no `gh`, use the curl fallback
(curl-fallback.md) for both.

```
gh label create devflow:backlog --description "A devflow parked feature" --color 5319E7
```

Write each body to a fresh file outside the repo — never a fixed path, which another
session or another user can reach first:

```
mktemp "${TMPDIR:-/tmp}/devflow-backlog.XXXXXX"
```

The path it prints is `<body file>` below. The body is the feature's own text, plus one
line `Parked from: <the feature this run built>`, never the whole original request.

```
gh api repos/{owner}/{repo}/issues -f title="<feature>" -F body=@<body file> -f 'labels[]=devflow:backlog' --jq .number
```

Remove it after each issue is filed.

**No block, `local`, or a `gh` failure:** write a file instead, one per parked feature, at
`.devflow/backlog/<short-name>.md`. Never park under a name a `Backlog:` line already holds
— step 1 would read that entry as built and delete it. Run both of step 1's lookups for
the name first, and on a hit from either pick another. If `gh` cannot answer, the name is
unchecked; use `<short-name>-<YYYY-MM-DD>` instead:

```markdown
# <feature>

<the feature's own text>

Parked from: <the feature this run built>
```

Either way, print exactly one line once every feature is parked:

```
✓ **parked** #46 add export, #47 fix login
```

```
✓ **parked** .devflow/backlog/add-export.md, .devflow/backlog/fix-login.md
```

**If `## Plans` said `github` and `gh` fails**, fall back to the file and say so instead
of the `parked` line, the same way step 4's plan falls back:

```
✗ **parked** github asked, wrote .devflow/backlog/<name>.md — gh said <the error>
```

**Then offer a chip per parked feature, if `mcp__ccd_session__spawn_task` is a tool you
have.** Chips come on top of parking, never instead of parking: the issue or the file is
the record, and a chip is one click to start it. A chip starts a new session in a fresh
worktree, and a fresh worktree has only committed files, so the prompt must stand alone:

- **Parked as an issue** — the prompt is `/devflow:flow #<n>`. The issue carries the text,
  and `submit` closes it.
- **Parked as a file** — the prompt is `/devflow:flow ` followed by the feature's own
  text, never the backlog path: the file is untracked here and not in that worktree. End
  it with one line, `Also parked as .devflow/backlog/<short-name>.md — delete it in this
  branch if it is there.` Step 1 reads that line, and `submit` turns it into a
  `Backlog:` line, so an entry the chip could not see is skipped later, not built twice.
- **This run's request was an issue or a backlog file** — offer no file-case chip. That
  text was not typed by the human, and a chip hands it to the next run as if it were,
  past step 1's guard. The file alone is the record; an issue-case chip is still fine,
  because the next run reads the issue through that guard.

Title each chip `Build <feature>`. Then print exactly one line:

```
✓ **chips** 2 offered — each starts its own flow run in a fresh worktree
```

**No such tool** — the CLI, the web — print nothing and offer nothing. The `parked` line
already said where each feature went.
