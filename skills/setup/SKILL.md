---
name: setup
description: Use when a project's CLAUDE.md has no `## Workflow` block, or the human asks to set devflow up. Reads the repo, detects the test, typecheck and lint commands and runs them to confirm they work, asks what the project is about and whether to work direct (commit on main) or pr (a branch and a pull request per job), then writes the Checks, Plans and Workflow blocks, and in a UI repo a Browser block, into the project CLAUDE.md. Called by flow first, when the Workflow block is missing.
---

# setup

Read the repo, ask how the human works here, work out this project's check commands,
**prove they run**, then write them down.

Run once per project. `flow` calls it first when `CLAUDE.md` has no `## Workflow` block. Run
it again if the commands change or the checks start behaving oddly.

Why these rules are what they are: [docs/setup.md](../../docs/setup.md). Read it only if a
rule looks wrong.

## 0. Read the repo before asking

Everything below that can be read is read first, and a question the repo already answers is
not asked. Run each bare, one per call:

```
gh api repos/{owner}/{repo} --jq .private
gh api repos/{owner}/{repo}/collaborators --jq length
gh api repos/{owner}/{repo}/branches/<default>/protection --silent
```

- Whether `.github/workflows` exists, and whether any workflow runs on a push to the default
  branch.
- A `403` or `404` on branch protection is "none", not an error.
- Deploy-on-push signs: `vercel.json`, `netlify.toml`, `railway.json`, `railway.toml`, or a
  workflow that deploys on a push to the default branch.
- No `gh`, or no GitHub remote: say "not read" for each GitHub fact and go on. Never guess one.

Print what you found, one shaped line each:

```
✓ **repo** private, 1 collaborator, no CI, no protection on main

✓ **deploy** vercel.json — a push to main may go live
```

## 1. Already set up?

Read the project's `CLAUDE.md` and look for a `## Checks` block.

If one exists, **do not overwrite it.** Run each command in it and print one shaped line per
command, the same shape step 3 uses below. Then:

- all pass → go to step 5 if there is no `## Plans` block yet
- one fails or is missing → print it `✗`, suggest a fix, and ask before changing anything

A block someone wrote deliberately is not yours to replace. The same goes for `## Plans` and `## Workflow`: if one is there, leave it, and only say what it says. A project with `## Checks` but no `## Workflow` is asked only step 6's questions.

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

## 6. How do you work here?

Ask in `AskUserQuestion` popups, by [flow's rules for asking](../flow/SKILL.md#asking-questions--rounds-until-no-answer-would-change-the-build):
the recommended option first, its label ending " (Recommended)", the tool's own "Other"
for free text. Where there is no popup tool, ask the same as a numbered list and take "yes to
all". Skip this step when `## Workflow` is already there, and only say what it says.

One round, two questions:

1. **What is this project about?** The recommended option is a one-line guess from the
   README, so "yes" is enough. The human's own words, typed into Other, win over the guess.
   Those words are what gets written, unedited.
2. **How should the work be done?** Two options:
   - `direct` — commit on main and push. No branch, no pull request.
   - `pr` — a branch and a pull request for each job.

   Recommend from what step 0 read. **Private, one collaborator and no CI → `direct`.**
   Anything else → `pr`. When a deploy-on-push sign was found, say so in the option's own
   text: "a push to main may go live". Still recommend `direct` when the rest says direct;
   review stays on for Standard and Deep work either way.

Write the block, exactly this shape, to the project's `CLAUDE.md`:

```markdown
## Workflow
- Mode: direct
- About: <one line, the human's own words>
```

`Mode:` is `direct` or `pr`. Step 6b may add a `- Servers:` line; nothing else goes in this
block. No block means "not set up", and every skill reads `Mode:` from here itself.

## 6a. A browser driver, in a UI repo

`submit` checks a UI change in a browser, and reads a `## Browser` block for the driver to
use ([browser-check.md](../submit/references/browser-check.md)). Skip this step with
`– **browser** skipped — no UI` when the repo has no UI, by the same read as
[the skills skill's step 3a](../skills/SKILL.md#3a-a-repo-with-a-ui) — and when a `## Browser`
block is already there, keep it and say what it says.

Otherwise ask one question, in the popup style of step 6:

1. **Which browser driver should checks use?**
   - Playwright CLI (Recommended) — it keeps a page's tree out of context, so a check costs
     fewer tokens than a browser MCP server. The reason goes in the option, in one line.
   - Research which fits me — start one `devflow:researcher`, giving it what the repo and
     this machine already have: the UI dependencies, any `playwright.config.*`, which browser
     CLIs are on the PATH and the browser tools this session has. Then recommend again, with
     what it found, and without this option. Start it only when the human picks this option.
   - Use whatever the session has — no preference. It writes `- Driver: session` and needs no
     proof, so the question is not asked again.
   - Other — the human types their own driver.

**Prove the driver runs.** For Playwright CLI that is `playwright-cli --version`, bare. For
another driver, its own version command. A driver that is a tool of this session, such as an
MCP server or the desktop browser pane, is proven by that tool being in the session.

**Not installed** → print the install command and stop at that. Setup installs nothing:

```
npm install -g @playwright/cli@latest
```

Write no block for a driver that did not run. The human installs it, and `flow` asks again on
its next run ([browser-driver.md](../flow/references/browser-driver.md)).

Proven → write the block, exactly this shape, to the project's `CLAUDE.md`:

```markdown
## Browser
- Driver: playwright-cli
```

One line. Nothing else goes in this block: login, URLs and traps stay in the project's own
`CLAUDE.md` notes. It is not a `## Checks` line, because `build` and `submit` run every one of
those as a command.

## 6b. Keep the dev server running?

`submit`'s live check starts the project's server, and stops it when it is done. A slow app
can ask for it to stay up instead ([live-check.md](../submit/references/live-check.md#a-kept-server)).
Skip this step with `– **servers** skipped — nothing starts a server` when the repo's live
check starts none (a library, a CLI, a one-shot script). When `## Workflow` already has a
`- Servers:` line, keep it and say what it says.

Otherwise read the start command (`package.json` scripts, a `Makefile` target, `Procfile`,
`docker-compose.yml`, or the README's own) and ask one question, in the popup style of step 6:

1. **Keep the dev server running after the live check?**
   - Keep the server running — for an app that starts slowly: several servers, a database, a
     heavy backend such as Medusa. You click through the PR without a wait.
   - Stop the server — for an app that starts in seconds. Today's behaviour.

   Mark the one the start command points to "(Recommended)". Keep applies in a local session
   only: in a cloud session the live check always stops its server, because the human's
   browser cannot reach the sandbox's localhost. Sweepers always stop too.

Write the answer as one line in the `## Workflow` block of step 6, `- Servers: keep` or
`- Servers: stop`. No line means stop.

**A start command that binds one fixed port** (`--port 3000`, `PORT=3000`, a port in the
dev script or its config) lets only one server run at a time, so a kept server blocks the
next live check. Print a recommendation and write nothing: a lane script. It picks the
lowest free lane, every port the app uses moves together, and the CORS or allowed-origins
list names every lane. The human's own `scripts/dev.sh` in bykare-medusa-admin is the
pattern. Then the live check reads the port the server printed, and never assumes one.

## 6c. Env files in every worktree

devflow makes many worktrees: `flow`'s step 0c, one per plan chain, one per sweeper. A
gitignored env file such as `.env` never reaches a new one, so a test that needs the database,
or a live check that starts the server, fails there for a reason the change did not cause.
Claude Code copies what a `.worktreeinclude` at the repo root names into every worktree it
makes with git: `claude --worktree`, the `EnterWorktree` tool, agents with `isolation: worktree`
and the desktop app's sessions ([Worktrees](https://code.claude.com/docs/en/worktrees#copy-gitignored-files-into-worktrees)).
It copies; it does not link.

When a `.worktreeinclude` is already there, keep it and say how many paths it lists:
`– **env** kept — .worktreeinclude lists 2 paths`.

Otherwise read the paths with `flow`'s `Env files` Context line, without its `head -20`: each
file or link named `.env*` in the main checkout, outside `node_modules`, `vendor`, `.venv` and
other worktrees, that git ignores. Never a `.env.example`, `.env.sample` or
`.env.template`: those are templates. None found → `– **env** skipped — no ignored env files`,
and write nothing.

**Paths only.** Never open, print or quote an env file — not in a question, a log, the PR or a
commit. Its path is all this step reads.

Ask one question, in the popup style of step 6, with the paths in its text:

1. **Copy these env files into every worktree Claude Code makes?**
   - Copy all of them (Recommended) — tests and the live check then work in a worktree as they
     do in the main checkout.
   - Never copy — for env files that hold keys an agent should not carry around.
   - Other — the human names the paths to copy.

Write `.worktreeinclude` at the repo root. It is committed, so the question comes once. Give
each path a leading `/`: in its `.gitignore` syntax a name with no slash matches at any depth,
so `.env` alone would copy `apps/api/.env` too.

```
# Copied into every worktree Claude Code makes. Paths only, never values.
/.env
/apps/api/.env
```

"Never copy" writes the file with one comment line, so it is not asked again:

```
# devflow: no env files are copied into worktrees.
```

Claude Code reads the file in the main checkout, so it takes effect once it is merged and
pulled there. A copy is made when the worktree is, so a value changed later does not reach a
worktree that already exists.

## 7. Report

Keep it short, one shaped line per fact:

```
✓ **checks** written to CLAUDE.md

✓ **test** pnpm test — pass (48 tests, 6s)

✓ **typecheck** pnpm typecheck — pass

✓ **lint** pnpm lint — pass

✓ **plans** github (labels devflow:plan, devflow:backlog exist)

✓ **workflow** direct (private, 1 collaborator, no CI)

✓ **browser** playwright-cli 0.1.22 (UI repo)

✓ **servers** keep (Medusa and a database start slowly)

✓ **env** .worktreeinclude lists 2 env files

– **deploy** not written — that is ship's to add
the first time it deploys and can prove the command works
```

The `checks` line says `written` only when step 4 wrote the block. Otherwise it is
`– **checks** kept — already in CLAUDE.md`, or `✗ **checks** not written — <why>`.

The `workflow` line says `kept` when `## Workflow` was already there. A `Mode:` the human
chose against the recommendation says so: `✓ **workflow** pr (direct was recommended)`.

Then mention, once, only if relevant:

- the project has no tests at all — worth knowing before trusting the flow
- a check took a long time
- the project is currently red

## 8. Offer agent skills

Last, after the report, ask one question in the same popup style as step 6, every time
setup runs:

1. **Look for agent skills that fit this repo?**
   - Yes (Recommended) — call `devflow:skills`. It reads what the repo is built with and
     what is already installed, then lists the skills that fit, each with its install
     command, and asks whether each review agent in `.claude/agents/` runs in review.
     Its list and those questions are the last thing setup prints.
   - No — print one line and stop:

     ```
     – **skills** skipped
     ```

`devflow:skills` only lists. Setup installs nothing either: the human runs each command.

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
- Never overwrite an existing `## Workflow` block. Say what it says and keep it.
- Never write `Mode:` as anything but `direct` or `pr`, and never write it without asking.
- Never add anything to `CLAUDE.md` except the `## Checks`, `## Plans`, `## Workflow` (with its `- Servers:` line, step 6b) and, in a UI repo, `## Browser` blocks, and never a block you did not prove. `- Driver: session` names no driver, so it has nothing to prove.
- Never print, quote or commit a value from an env file. Step 6c reads paths only, and writes them to `.worktreeinclude`.
- Never run an install, the browser driver's included: step 6a prints its command. Step 8 offers `devflow:skills`, which only lists; the human installs.

## Where the shape came from

The questionnaire takes its shape from the `setup-matt-pocock-skills` skill in
[mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md)
(MIT): read the repo first, print what it shows, ask one section at a time with the
recommended answer first, skip a question the repo already settled, then write a block into
`CLAUDE.md`. Where it differs: the recommendation here is read from the repo's own facts
(visibility, collaborators, CI), the one question that matters is `direct` or `pr`, and
`flow` calls it on its own when the block is missing.
