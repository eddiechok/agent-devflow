---
name: setup
description: Prepare a project to use devflow. Detects the test, typecheck and lint commands, runs them to confirm they actually work, then writes a Checks block into the project CLAUDE.md. Also asks where Deep plans live, in a file or on GitHub, and writes a Plans block. Run once per project, or again when the commands change.
disable-model-invocation: true
---

# setup

Work out this project's check commands, **prove they run**, then write them down.

Run once per project. Run again if the commands change or the checks start behaving oddly.

Why these rules are what they are: [docs/setup.md](../../docs/setup.md). Read it only if a
rule looks wrong.

## 1. Already set up?

Read the project's `CLAUDE.md` and look for a `## Checks` block.

If one exists, **do not overwrite it.** Run each command in it and print one shaped line per
command, the same shape step 3 uses below. Then:

- all pass → go to step 5 if there is no `## Plans` block yet
- one fails or is missing → print it `✗`, suggest a fix, and ask before changing anything

A block someone wrote deliberately is not yours to replace. The same goes for `## Plans`: if it is there, leave it, and only say what it says.

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

**Run every command you found and show the output.**

Run each one **bare**, exactly as you would write it into the block, one command
per call. No pipes, no redirects, no `&&`, no `; echo $?`.

For each, print one shaped line, labelled by its row:

```
✓ **test** pnpm test — pass (48 tests, 6s)
```

```
✗ **typecheck** pnpm typecheck — fail
```

```
– **lint** not found
```

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

Do not add a `Makefile` or an npm script to make the block tidier — that is changing the project to suit the tool.

## 5. Where do plans live?

Deep work writes a plan. It can live in a file, `.devflow/plans/<name>.md`, or as a GitHub issue. The project decides. Ask once, with the recommendation attached:

```
Where should Deep plans live?
   -> Recommend: local (.devflow/plans/). Pick github if you want plans
      visible as issues, closed on merge, and listed as a backlog.
```

**Local is the default.** No answer, or no block, means local. Nothing downstream needs the block to exist.

**Picking github means two things, and say both out loud:**

- A cloud session does not come with `gh`. Add `apt-get update && apt-get install -y gh` to the cloud environment's setup script, and plans on GitHub work there too. Without it, runs there fall back to `curl`, and to a local file for that job only if `curl` fails too, and say so.
- Anyone who can edit the issue can edit the plan, and a plan is an order to `build`. Fine on your own repos. Think twice on a public one.

**Prove it before writing it.** Same rule as the checks. For github, run this bare:

```
gh api 'repos/{owner}/{repo}/issues?per_page=1' --jq length
```

With no `gh` installed, run the same read with `curl`, owner and repo from
`git remote get-url origin`. If the remote does not name a GitHub repo, write them in
yourself:

```
curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN" "https://api.github.com/repos/<owner>/<repo>/issues?per_page=1"
```

Never print `$GH_TOKEN`, and send it to `api.github.com` and no other host.

It must answer with a number, or with the JSON list for `curl`. An error means no auth or no remote — or, with no `gh`, that the `curl` read failed too — and that is not a project you can write `github` for. Say which, and **write no `## Plans` block at all**.

Then make sure the label exists. A plan issue carries `devflow:plan`, and `flow` looks for it by that label:

```
gh label create devflow:plan --description "A devflow Deep plan" --color 0E8A16
```

With no `gh` installed, make it with `curl` instead:

```
curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN" -d '{"name": "devflow:plan", "description": "A devflow Deep plan", "color": "0E8A16"}' https://api.github.com/repos/<owner>/<repo>/labels
```

An error that says the label already exists is fine — from `curl` it is a `422` with
`already_exists`. Any other error, stop:

```
✗ **plans** label not made — gh said <the error>
```

Then make the second label the same way. `flow` parks extra features there, one feature per run, filing each one it does not build under `devflow:backlog`:

```
gh label create devflow:backlog --description "A devflow parked feature" --color 5319E7
```

With no `gh`, the same `curl` call makes it, with this label's name, description and
color. Same error rule: "already exists" is fine, any other error means stop and say so.

Write the block:

```markdown
## Plans
- Tracker: github
```

Or `local`. One line, one value. Nothing else goes in this block.

## 6. Report

Keep it short, one shaped line per fact:

```
✓ **checks** written to CLAUDE.md

✓ **test** pnpm test — pass (48 tests, 6s)

✓ **typecheck** pnpm typecheck — pass

✓ **lint** pnpm lint — pass

✓ **plans** github (labels devflow:plan, devflow:backlog exist)

– **deploy** not written — that is ship's to add
the first time it deploys and can prove the command works
```

The `checks` line says `written` only when step 4 wrote the block. Otherwise it is
`– **checks** kept — already in CLAUDE.md`, or `✗ **checks** not written — <why>`.

Then mention, once, only if relevant:

- the project has no tests at all — worth knowing before trusting the flow
- a check took a long time
- the project is currently red

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never write a command you have not run.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never overwrite an existing `## Checks` block without asking.
- Never invent a command to fill a row. Missing is better than wrong.
- Never write `Tracker: github` without that REST read having answered in this run.
- Never add anything to `CLAUDE.md` except the `## Checks` and `## Plans` blocks, and never a block you did not prove.
