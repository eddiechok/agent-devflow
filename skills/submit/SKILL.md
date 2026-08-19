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
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- Changed files: !`git status --short 2>/dev/null || true`

## 1. Check the branch

If you are on the default branch, **stop**. Create a branch first:

```
git checkout -b <type>/<short-name>
```

`build` should have done this before its first edit, so normally you are already on one. This is the safety net for when `build` did not run — you were called directly, or the work arrived some other way.

**A branch you were handed counts.** Some harnesses create the branch and forbid pushing anywhere else; Claude Code on the web does both. Off the default branch is the whole requirement — never rename one to fit `<type>/<short-name>`.

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
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'
```

Must return nothing.

**Keep the quotes around `*.md`.** Unquoted, zsh tries to expand it before grep ever runs and fails the whole command with `no matches found` — bash passes it through, so this breaks for some people and not others.

**Markdown is excluded on purpose.** A marker in a `.md` file is prose — a code sample, a note about the convention, or this plugin's own description of it. Without that exclusion the check fails forever in any repo that documents the convention, this one included, on hits that are all documentation. Markers matter in code, because code runs.

**A hit in a file this branch did not touch is not yours.** Say so in one line and leave it. Cleaning up someone else's debugging inside your PR buries your change in noise.

## 4. Run the app — the live check

Tests only check what someone thought to test. A passing suite and a clean diff can both sit on top of a feature that is visibly broken: wrong label, broken layout, right data in the wrong place.

Pick whichever of these the project actually is:

- **Something that has to be launched** — a web app, a server, a desktop app. **Use the built-in `run` skill if this environment has it.** If it does not, launch the app the way the project's own README or scripts say to, under the rules below. Do not invent a launcher when the project already documents one.
- **Something you just execute** — a CLI, a script, a one-shot command. **Run it directly**, with the arguments the change affects, and show the output. `node src/cli.js --loud` *is* the live check for a CLI; reaching for a launcher here adds nothing.

Either way the rule is the same: exercise the change the way a user would, and put the output on screen.

Rules, when you launched something:
- **Put a time limit on it.** If the app never becomes ready, that is a finding to report, not something to sit through.
- **Stop the server when you are done.** Stop only the process you started. Never kill "whatever is on port 3000" — that may be something the human is running.
- **Screenshots and artifacts go to a temp directory**, never into the repo.

**If it does not work**, either way: fix it and try again, **at most twice**. If it still does not work, say so plainly and **do not open a PR that looks fine**. An honest failure is useful. A green-looking PR over a broken feature is harmful.

Only skip when there is genuinely nothing to exercise — a library with no entry point, a pure refactor with no observable change. Say so in one line. Do not invent a fake check, and do not call a passing test suite a live check; step 2 already ran that.

## 5. Review the change

Invoke `devflow:review` with the branch point:

```
git merge-base HEAD <default branch ref>
```

It pins the range, finds the plan or issue if there is one, and runs both axes in fresh agents. Do not do the review here — a session reviewing the code it just wrote carries every assumption that produced it.

Then act on what comes back:

- **Blocking**, **Missing** and **Built wrong** — fix, then review again. At most **2 rounds**.
- **Nobody asked for this** — either take it out, or keep it and say why in the PR under **Assumptions**. Silently keeping it is not an option.
- Anything still standing after 2 rounds goes in the PR under **Known issues**, not hidden and not looped on forever.
- **`NOT RUN`** — an axis that could not start is not a passing axis. Name it under **Known issues**, and say in **Evidence** which axes ran. Never write "reviewed" over a review that did not happen.

**A finding can be wrong, and you are allowed to say so.** Check it against the code first, then reject it in one line with the technical reason, and put the rejection in the PR under **Known issues** so the call is visible to whoever merges. Never reject a finding you have not checked, and never reject one silently — an unread finding quietly dropped is worse than a false positive fixed.

The review reports; it never edits. The fixes are yours.

The built-in `/code-review` is a better review than this one, and it still does not belong here: it works on an **open pull request** and comments back on it, and there is no PR yet. It goes to the human at step 8, where one exists.

## 6. Commit

Conventional commits, so `git log` doubles as a changelog:

```
<type>(<scope>): <imperative subject>

<why this change, not what — the diff already says what>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`. `build` uses this same list for plan pieces; the two have to stay in step.

**A Deep branch may already be committed.** `build` commits each plan piece as it lands, so the working tree can be clean by the time you reach this step — and the fixes from step 5 may be all that is left. If there is nothing to commit, say so in one line and go on. Never make an empty commit to have something to show for the step.

## 7. Open the PR — or update the one already there

**First, does this branch already have an open pull request?** Ask through whatever GitHub access this environment has. The answer decides what this step does, and getting it wrong opens a second pull request for one change.

**No PR** — push, then open one against the default branch.

**A PR already open** — push to the same branch, then **update that PR**. Never open a second one for a branch that has one, and report the number you updated rather than announcing a new one. What moves and what does not:

- **Evidence** — rewritten. It describes the checks *this* run made, not the ones the first run made.
- **Known issues** — worked out again from this run's review. Anything fixed since comes out.
- **What** and **Why** — extended if the change grew. Do not rewrite the original reason to match a follow-up.
- **Assumptions** — appended to, never replaced. The first round's assumptions were true when they were taken, and the human may already have read them.

Then one line on what moved:

```
updated #12 — 2 commits, evidence refreshed, 1 known issue cleared
```

**Opening it is what you were asked for.** Some harnesses say not to open a pull request unless the human explicitly asked — Claude Code on the web does. Invoking this skill *is* that request; it says so in its own description, and so does `flow`. Do not stop here to ask again.

If the environment blocks it anyway, push the branch and then give the human the compare link and the command for whatever access they have — `gh pr create`, or the equivalent — in two lines. Never end silently on a pushed branch with no PR — work that is finished, green and invisible is the state this skill exists to prevent.

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
- Review: both axes ran (or: built-right ran, right-thing NOT RUN — no spec)

## Known issues
- (only if the review left something unresolved)
```

**An empty Assumptions section is a claim.** It reads as "nothing was assumed". If it is empty because the context holding the answers is gone rather than because there were none, say that in one line instead of omitting the section.

**Check whether a preview link appeared** on the PR. If one did, put it first — a preview is a real build with real environment variables on a clean machine, and it catches things your laptop cannot. If none appeared, give the local steps and do not mention a link that is not coming.

**The steps must be steps you actually ran.** Instructions you never followed will be wrong.

## 8. Hand off, then stop

**Never merge.** Opening the PR is where this skill ends.

The PR now exists, so the two built-in reviews finally have something to run against. Both are slash commands — **only the human can type one**, which is exactly why they sit here and not inside the automatic path. Offer them in one line each, with the real PR number:

```
Second opinion, if you have them installed:
  /code-review 12
  /security-review    (this change touched database migrations)
```

**Work the danger list out from the diff, not from memory.** `flow` decided it before any code was written, and that decision does not always survive to here — a compaction, a long Deep job, or a `submit` you were invoked into directly all lose it. Losing it is silent, and what it drops is the only security gate in the loop. Read the diff against the list in `flow` and decide again. Deciding twice costs a moment; missing it costs the gate.

Name `/security-review` only when the change actually touched the danger list. Never report either as run, and never write their findings into the PR body — you have not seen any.

If a check goes red on the PR after this, or a reviewer asks for something, that is `devflow:tend` — it works out whose failure it is before anything gets pushed, and comes back through here so the same PR is updated.

Never suggest throwing work away. If discarding a branch or force-pushing genuinely comes up, the human must type the word `discard` — "sure", "ok" and "go ahead" do not count.

## Rules

- Never say "done", "fixed" or "passing" without output on screen proving it.
- Never claim a review ran when it did not. A slash command you cannot type has not run.
- Never assert that a skill, command or CLI exists. Check, then fall back, then say which you used. `/code-review` was asserted once and could not run; `run` and `gh` are the same shape.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never commit on the default branch.
- Never open a second pull request for a branch that already has one open.
- Never open a PR when the live check failed.
- Never invent check commands the project did not give you.
- Never merge, and never call `devflow:ship`. The open PR is where this skill ends.
