---
name: setup
description: Prepare a project to use devflow. Detects the test, typecheck and lint commands, runs them to confirm they actually work, then writes a Checks block into the project CLAUDE.md. Run once per project, or again when the commands change.
disable-model-invocation: true
---

# setup

Work out this project's check commands, **prove they run**, then write them down.

Run once per project. Run again if the commands change or the checks start behaving oddly.

## Why this matters

Everything downstream trusts the `## Checks` block. `build` runs it after every change, `submit` runs it fresh before opening a PR, and the output hook keys off it.

A wrong or stale command here fails **silently**: `submit` runs something harmless, sees exit 0, and reports the work as proven. That is the worst kind of failure in this plugin, so nothing gets written to `CLAUDE.md` until it has actually been run.

## 1. Already set up?

Read the project's `CLAUDE.md` and look for a `## Checks` block.

If one exists, **do not overwrite it.** Run each command in it and report:

- all pass → say so in one line and stop
- one fails or is missing → say which, suggest a fix, and ask before changing anything

A block someone wrote deliberately is not yours to replace.

## 2. Work out the commands

Find the project's manifest and read the real script names. Do not guess from convention.

| Look for | Read |
|---|---|
| `package.json` | the `scripts` object. Use the package manager implied by the lockfile: `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, else `npm` |
| `pyproject.toml`, `setup.py`, `tox.ini` | pytest, ruff, mypy config |
| `go.mod` | `go test ./...`, `go vet ./...` |
| `Cargo.toml` | `cargo test`, `cargo clippy` |
| `Makefile` | targets named test, check, lint, build |
| `Gemfile`, `composer.json`, `*.csproj`, `build.gradle`, `pom.xml` | the equivalent |

Notes that matter:

- **A monorepo may have several.** Ask which package the human works in rather than picking one.
- **Not every project has all three.** A JavaScript project with no TypeScript has no typecheck. That is fine — omit the line. Do not invent a command to fill the row.
- **Prefer the narrow command.** `pnpm test` beats `pnpm test:all` if the second one also builds and deploys.

## 3. Run each one

This is the point of the skill. **Run every command you found and show the output.**

Run each one **bare**, exactly as you would write it into the block, one command
per call. No pipes, no redirects, no `&&`, no `; echo $?`. The bash hook trims
the output and prints `exit=N` itself, which is the pass/fail signal you need
here — but only for a plain command. Shape it yourself and the hook steps aside,
and you are back to reading a wall of output and guessing the exit code.

This matters more here than anywhere: a command you cannot read the exit code of
is a command you have not really proven, and proving them is the whole job.

For each: report `pass`, `fail`, or `not found`.

- **Fails because the code is broken** → still a valid command. Record it, and say the project is currently red.
- **Fails because the command does not exist** → wrong command. Find the right one.
- **Takes longer than a couple of minutes** → say so. A slow check will make every job slow, and the human may want a faster subset.

If you cannot find a working test command at all, say that plainly. Do not write a `## Checks` block with a command you never got to run.

## 4. Write it

Append to the project's `CLAUDE.md`, creating the file if needed:

```markdown
## Checks
- Test: pnpm test
- Typecheck: pnpm typecheck
- Lint: pnpm lint
```

Only include lines you actually ran. Three is typical, one is fine.

**A line may repeat.** Some projects have two test commands and no wrapper that runs both. Write both, and everything downstream runs them in order:

```markdown
## Checks
- Test: python3 hooks/test-bash-guard.py
- Test: python3 skills/test-frontmatter.py
```

Two honest lines beat one invented wrapper script. Do not add a `Makefile` or an npm script to make the block tidier — that is changing the project to suit the tool.

## 5. Report

Keep it short:

```
Checks written to CLAUDE.md.
  Test:      pnpm test        pass (48 tests, 6s)
  Typecheck: pnpm typecheck   pass
  Lint:      pnpm lint        pass

No ## Deploy block written — that is ship's to add, the first time it
deploys and can prove the command works.
```

Then mention, once, only if relevant:

- the project has no tests at all — worth knowing before trusting the flow
- a check took a long time
- the project is currently red

## Rules

- Never write a command you have not run.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never overwrite an existing `## Checks` block without asking.
- Never invent a command to fill a row. Missing is better than wrong.
- Never add anything to `CLAUDE.md` except the `## Checks` block.
