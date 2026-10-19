# A rule for an always-loaded file

Read this before any edit that adds a rule to an always-loaded file: `CLAUDE.md`,
`CLAUDE.local.md`, `AGENTS.md`, or a file under `.claude/rules/`. It holds for every change
— one the human asked for, a fix in `submit`'s loop, a project fact at `submit` step 6.

**A rule there becomes a script with a test.** The file gets a one-line pointer to it —
a `- Test:` line in `## Checks`, or a line naming the script.

**Only a rule no script can check stays as prose** — a matter of judgment — and then as one
short line.

**A human who asks for it as text in the file wins.** Write it as they asked.
