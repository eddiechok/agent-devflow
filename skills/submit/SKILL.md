---
name: submit
description: Use when the code is finished and ready to become a pull request. Runs the project checks fresh, runs the app to confirm the change really works, writes a conventional commit, and opens a PR with steps for the human to check it. Never merges; merging is what the ship skill does, and only a human starts that.
argument-hint: "[optional note for the PR title]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*)
---

# submit

Prove it works. Then open the PR. Never merge.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' | grep . || echo main`
- Changed files: !`git status --short 2>/dev/null || true`

## 1. Check the branch

If you are on the default branch, **stop**. Create a branch first:

```
git checkout -b <type>/<short-name>
```

`build` should have done this before its first edit, so normally you are already on one. This is the safety net for when `build` did not run — you were called directly, or the work arrived some other way.

Never commit directly to the default branch.

## 2. Run the checks fresh

Run the project's test, typecheck and lint commands from the `## Checks` block in `CLAUDE.md`.

**Run them now, in this turn. Not "they passed earlier".**

**Run each one bare** — exactly as the Checks block writes it, one command per
call. No pipes, no redirects, no `&&`, no `; echo $?`.

The real output **and the exit code** both have to reach the screen: the exit
code is what proves the run happened, and an outer loop watching this session
can only see what you actually printed. Running bare is how you get both — the
hook trims the output and prints `exit=N` for you. Shape the command yourself
and the hook steps aside by design, taking the trimming and the exit line with
it. `${PIPESTATUS[0]}` after a `;` silently printed nothing in a real run,
because the shell was not the one that syntax assumes.

If anything fails, fix it and run again. Do not continue with a red check.

## 3. Remove debug leftovers

```
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git
```

Must return nothing.

## 4. Run the app — the live check

Tests only check what someone thought to test. A passing suite and a clean diff can both sit on top of a feature that is visibly broken: wrong label, broken layout, right data in the wrong place.

Pick whichever of these the project actually is:

- **Something that has to be launched** — a web app, a server, a desktop app. **Use the built-in `run` skill.** Do not write your own launcher.
- **Something you just execute** — a CLI, a script, a one-shot command. **Run it directly**, with the arguments the change affects, and show the output. `node src/cli.js --loud` *is* the live check for a CLI; reaching for a launcher here adds nothing.

Either way the rule is the same: exercise the change the way a user would, and put the output on screen.

Rules, when you launched something:
- **Put a time limit on it.** If the app never becomes ready, that is a finding to report, not something to sit through.
- **Stop the server when you are done.** Stop only the process you started. Never kill "whatever is on port 3000" — that may be something the human is running.
- **Screenshots and artifacts go to a temp directory**, never into the repo.

**If it does not work**, either way: fix it and try again, **at most twice**. If it still does not work, say so plainly and **do not open a PR that looks fine**. An honest failure is useful. A green-looking PR over a broken feature is harmful.

Only skip when there is genuinely nothing to exercise — a library with no entry point, a pure refactor with no observable change. Say so in one line. Do not invent a fake check, and do not call a passing test suite a live check; step 2 already ran that.

## 5. Review the diff

Run the built-in `/code-review` on the change. It is already installed and it is better than anything this skill would improvise.

If it reports something serious, **fix it and review again**. At most **2 rounds**. Anything still outstanding after that goes in the PR under **"Known issues"** rather than being hidden or looped on forever.

If the change touched anything on the danger list, also run the built-in `/security-review`.

## 6. Commit

Conventional commits, so `git log` doubles as a changelog:

```
<type>(<scope>): <imperative subject>

<why this change, not what — the diff already says what>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.

## 7. Open the PR

Push, then open a PR against the default branch.

If the repo has a PR template, follow its headings. Otherwise use this shape:

```markdown
## What
One or two sentences.

## Why
The reason, or the issue it closes.

Closes #123

## Assumptions
- Took the recommendation on X, because no answer was given
(omit this section entirely if there were none)

## How to check this yourself

Preview: <link, if one appeared on the PR>
(Preview data source: unknown. If pages look empty, check locally instead.)

1. `pnpm dev`
2. Go to http://localhost:3000/settings
3. Turn on the setting and save
4. It should stay on after a refresh
5. Ctrl-C to stop the server when you are done

I checked this locally before pushing. I stopped my own server; step 5 is for yours.

## Evidence
- Tests: 48 passed, exit 0
- Typecheck: clean
- Live check: done, works

## Known issues
- (only if the review left something unresolved)
```

**Check whether a preview link appeared** on the PR. If one did, put it first — a preview is a real build with real environment variables on a clean machine, and it catches things your laptop cannot. If none appeared, give the local steps and do not mention a link that is not coming.

**The steps must be steps you actually ran.** Instructions you never followed will be wrong.

## 8. Stop

**Never merge.** Opening the PR is where this skill ends.

Never suggest throwing work away. If discarding a branch or force-pushing genuinely comes up, the human must type the word `discard` — "sure", "ok" and "go ahead" do not count.

## Rules

- Never say "done", "fixed" or "passing" without output on screen proving it.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never commit on the default branch.
- Never open a PR when the live check failed.
- Never invent check commands the project did not give you.
- Never merge, and never call `devflow:ship`. The open PR is where this skill ends.
