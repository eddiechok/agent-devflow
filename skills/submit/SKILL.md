---
name: submit
description: Use when the code is finished and ready to become a pull request. Runs the project checks fresh, runs the app to confirm the change really works, writes a conventional commit, and opens a PR with steps for the human to check it. Never merges; merging is what the ship skill does, and only a human starts that.
argument-hint: "[request: the words the human typed, passed on to review as the spec]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*)
---

# submit

Prove it works. Then open the PR. Never merge.

Why these rules are what they are: [docs/submit.md](../../docs/submit.md). Read it only if a
rule looks wrong.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- Changed files: !`git status --short 2>/dev/null || true`

## 1. Check the branch

If you are on the default branch, **stop**. Create a branch first:

```
git checkout -b <type>/<short-name>
```

**A branch you were handed counts.** Off the default branch is the whole requirement — never rename one to fit `<type>/<short-name>`.

Never commit directly to the default branch. Then print, unless `build` printed one this run:

```
✓ **branch** <name>
```

## 2. Run the checks fresh

Run the project's test, typecheck and lint commands from the `## Checks` block in `CLAUDE.md`.

**The checks must postdate the last edit.**

**One exception, and it is narrow.** If `build` ran **every command in the `## Checks` block**, in this session, so that its output is already on this screen, and no file has changed since — then that output is this step's output. Print `✓ **checks** <n> of <n> pass, exit 0 — build's run, no edit since` and go on. It does not apply on a Deep job: the builders ran the checks inside their own agents, and five lines came back, not output. Nor when `build` ran the suite but not the lint; `build`'s handback rule only promises the suite. Any edit since, including one you made a moment ago, means run them again.

**Run each one bare** — exactly as the Checks block writes it, one command per
call. No pipes, no redirects, no `&&`, no `; echo $?`.

The real output **and the exit code** both have to reach the screen.

Running bare is what lets the hook help.

**But the hook only knows the runners on its own list** — `npm test`, `pytest`,
`cargo test`, `tsc` and friends. So run it bare, read the result, and **say the
outcome in words** — "exit 0", "failed, 2 cases" — rather than waiting for a
line that is not coming. Never write `exit=0` yourself as though the hook
printed it.

If anything fails, fix it and run again. Do not continue with a red check. Once every
command is green, print:

```
✓ **checks** 3 of 3 pass, exit 0
```

## 3. Remove debug leftovers

```
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'
```

Must return nothing.

**Keep the quotes around `*.md`.**

**A hit in a file this branch did not touch is not yours.** Print `– **debug** <file> — not this branch's, left in place`.

Once it returns nothing:

```
✓ **debug** none found
```

## 4. Run the app — the live check

Pick whichever of these the project actually is:

- **Something that has to be launched** — a web app, a server, a desktop app. **Use the built-in `run` skill if this environment has it.** If it does not, launch the app the way the project's own README or scripts say to, under the rules below. Do not invent a launcher when the project already documents one.
- **Something you just execute** — a CLI, a script, a one-shot command. **Run it directly**, with the arguments the change affects, and show the output.

Either way the rule is the same: exercise the change the way a user would, and put the output on screen.

### What counts as proof

**The test is one question: would this have been true before the change?** If yes, it
proves nothing.

- **First-hand** — the thing you are claiming, observed. The response body with the new
  field in it. The page text showing the new label. The CLI's actual stdout for the flag
  you added. A screenshot of the layout you fixed.
- **Second-hand** — true either way. A `200`. A green pipeline. "Server started". An exit
  code. "Tests passed" — step 2 already ran those, and a suite that never covered this
  change passes just as loudly.

**Only first-hand ends this step.** Go and look at the thing itself.

Rules, when you launched something:
- **Put a time limit on it.** If the app never becomes ready, that is a finding to report, not something to sit through.
- **Stop the server when you are done.** Stop only the process you started. Never kill "whatever is on port 3000" — that may be something the human is running.
- **Screenshots and artifacts go to a temp directory**, never into the repo.

**If it does not work**, either way: fix it and try again, **at most twice**. If it still does not work, print `✗ **live** <what failed>` and **do not open a PR that looks fine**.

Only skip when there is genuinely nothing to exercise — a library with no entry point, a pure refactor with no observable change. Print `– **live** nothing to exercise — <reason>`. Do not invent a fake check, and do not call a passing test suite a live check; step 2 already ran that.

Otherwise, once you have looked at the thing itself:

```
✓ **live** POST /settings returns the new field
```

## 5. Review the change

Invoke `devflow:review` with the branch point:

```
git merge-base HEAD <default branch ref>
```

**Pass it the request text too, if you were given one.** `flow` hands it over at its step 5 as `request: <text>`, word for word; hand it to `review` in the same form, after the fixed point. If you were invoked directly and have no request, say so in one line and let the axis skip — do not write one from memory of the diff.

**Pass `no-behaviour: <reason>` too, when `build` said there was nothing to test.** `build` has one gate for that, and it prints `– **no-behaviour** <reason> — running the checks instead`. Hand that reason on **as its own line**, `no-behaviour: <reason>`, after the fixed point and the request — `review` recognises it only at a line start. `review` then starts no agent and reports all three sections as `skipped — no behaviour`, which you read as **nothing to fix**: no findings, no rounds, nothing for **Known issues**, and `Review: skipped, no behaviour` under **Evidence** at step 8.

Only `build` decides this, and only for the change in front of it. If `build` ran the gates, the axes run — never reach for the exit yourself because the diff looks small or because it is all markdown.

Do not do the review here — a session reviewing the code it just wrote carries every assumption that produced it.

Then act on what comes back:

- **Blocking**, **Missing** and **Built wrong** — fix, then review again. At most **2 rounds**.
- **Round 2 is scoped, not a fresh review.** It goes to the axis agent directly — `devflow:reviewer`, or `devflow:spec-reviewer` for its own findings — with the fixed point, round 1's findings in the agent's own words, and the files changed since.
- **Nobody asked for this** — either take it out, or keep it and say why in the PR under **Assumptions**. Silently keeping it is not an option.
- Anything still standing after 2 rounds goes in the PR under **Known issues**, not hidden and not looped on forever.
- **The last review must postdate the last edit.** A fix you make after the last round is an edit nobody has read, and so is a doc fix at step 6. Both get one short look at step 7, before the commit. It is a look, not a round.
- **`NOT RUN`** — an axis that could not start is not a passing axis. Name it under **Known issues**, and say in **Evidence** which axes ran. Never write "reviewed" over a review that did not happen.
- **`Not reported: N further findings`** — the axis ran out of room. Those findings exist and you have not seen them. **Run that axis again, scoped to what it did not reach**, and if the second run is also truncated, say so under **Known issues** with the count.

**A finding can be wrong, and you are allowed to say so.** Check it against the code first, then reject it in one line with the technical reason, and put the rejection in the PR under **Known issues** so the call is visible to whoever merges. Never reject a finding you have not checked, and never reject one silently — an unread finding quietly dropped is worse than a false positive fixed.

**The `Challenged` section is help with exactly that call, not a decision already made.**

- **Falls** — `hardcase` found the line that refutes it. **Check that line yourself**, then reject the finding with its reason.
- **Stands** — a finding that survived an agent whose whole job was to break it. Fix it. Rejecting one of these takes more than a one-line reason, and you had better be able to say what both of them missed.
- **Could not check** — the challenge did not happen for that finding. Treat it exactly as if there had been no challenge at all. It is not a `Falls`.

Never write "challenged" over a `hardcase` that did not run, and never let a `Falls` you did not verify take a fix off the list.

The review reports; it never edits. The fixes are yours. Once it is settled, print one line that names what was found:

```
✓ **review** 2 found, 2 fixed — a loose test scanner, a stop line with no mark
```

or, when `build` said there was nothing to test:

```
– **review** skipped, no behaviour
```

## 6. Update the docs the change made stale

Find the docs that describe what changed: the README, anything under `docs/`, `CLAUDE.md`, and the description of any skill or agent the change touched. Read the parts that talk about this behaviour. If a doc now says something the code no longer does, fix it here, on this branch, so the doc lands in the same pull request as the code that dated it.

The bar is narrow: a doc that is now **wrong**, not a doc that could say more. Do not write new pages, and do not touch a doc the change did not date. A line beside the code that dated it is the whole step; anything bigger goes back through `flow` as its own request.

**Then say what you did, in one line.** Name each file and what was stale in it:

```
✓ **docs** README.md — the cleanup bullet claimed flow removes every worktree
```

And say so when nothing was, in those words, rather than going quiet:

```
– **docs** nothing stale
```

**A step that prints nothing cannot be told from a step that was skipped** — not in the transcript, not in the commit, not by whoever reads the pull request, and not by you on a second pass through this skill. Every other step here leaves a line for that reason. This one is the step most easily lost on a follow-up, because the docs were already right the first time round.

## 7. Commit

**If any file changed since step 2's run, run the checks again first.** Same rule as step 2: the checks must postdate the last edit. Bare, one per call, output on screen.

**If any file changed since the last review that read it, one short look first.** Round 2 counts as a read of the lines it was scoped to. `devflow:reviewer` only, scoped to the lines that changed, a **200 word ceiling**, and no `hardcase`.

**If the look finds something new, it gets at most one bounded fix.** Two conditions, and both have to hold:

- **Small** — a few lines, the kind of fix that takes a minute.
- **In a file already changed on this branch.**

Both hold → fix it, run the `## Checks` block again — bare, one per call, as at step 2 — and stop. **No further look.** Either fails — a bigger fix, or a file the branch did not touch — → **stop editing** and put it under **Known issues**, as before. Print which of the two happened, in one line:

```
✓ **look** fixed in place — skills/ship/SKILL.md, 2 lines
```

```
– **look** known issue — docs/pipeline.md, not on this branch
```

When nothing changed since the last review, there is no look to run:

```
– **look** nothing changed since the last review
```

A fix made here is the one edit on the branch no agent has read. Name it in the PR body under **Evidence**, in these words — `Final look: fixed <file>, <what> — unread by an agent, so read those lines yourself` — because the reader is the only one who can read them now. The loop stays bounded: review, round 2, look, at most one small fix, done.

Conventional commits, so `git log` doubles as a changelog:

```
<type>(<scope>): <imperative subject>

<why this change, not what — the diff already says what>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`. `build` uses this same list for plan pieces; the two have to stay in step.

**A request with an `Also parked as .devflow/backlog/<name>.md` line** came from a `flow`
chip. End the commit body with `Backlog: .devflow/backlog/<name>.md`, and put the same line
under **What** in the PR body — whether or not the file was in this checkout. With nothing
to commit, the PR body alone carries it. It is what a later `flow` run looks for before
building that file, so a feature ships once.

**A Deep branch may already be committed.** If there is nothing to commit, print `– **commit** nothing to commit — already committed by build` and go on. Never make an empty commit to have something to show for the step.

Otherwise, once the commit is in:

```
✓ **commit** feat(settings): read the flag in the API (a1b2c3d)
```

## 8. Open the PR — or update the one already there

**First, does this branch already have an open pull request?** Ask through whatever GitHub access this environment has.

**No PR** — push, then open one against the default branch, then print:

```
✓ **pr** opened #14
```

**A PR already open** — push to the same branch, then **update that PR**. Never open a second one for a branch that has one, and report the number you updated rather than announcing a new one. What moves and what does not:

- **Evidence** — rewritten. It describes the checks *this* run made, not the ones the first run made.
- **Known issues** — worked out again from this run's review. Anything fixed since comes out.
- **What** and **Why** — extended if the change grew. Do not rewrite the original reason to match a follow-up.
- **Assumptions** — appended to, never replaced.

Then one line on what moved:

```
✓ **pr** updated #12 — 2 commits, evidence refreshed, 1 known issue cleared
```

**Opening it is what you were asked for.** Invoking this skill *is* the request; it says so in its own description, and so does `flow`. Do not stop here to ask again.

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
- Review: both axes ran — is it built right, and is it the right thing (or: built right ran, right thing NOT RUN — no spec; or: skipped, no behaviour)
- Final look: fixed skills/ship/SKILL.md, 2 lines — unread by an agent, so read those lines yourself (or: nothing new; or: omit if no look ran)

## Known issues
- (only if the review left something unresolved)
```

**A plan issue closes with the PR.** Only if the project's `## Plans` block says `github` and this work has a `devflow:plan` issue. Then name it under **What** — `Plan: #45` — and add `Closes #45` under **Why**, beside the request issue if there is one. Find the number on the `✓ **plan** #N` line `flow` printed, or by listing open `devflow:plan` issues and matching the subject. Do not guess a number, and write nothing about a plan issue on a project that keeps plans in files.

**A Deep branch carries assumptions in its commits too.** Each `builder` writes any doubt
it had about a finished piece as a `Concern:` line in that piece's commit body, because
the session that printed it may have been cleared since. Read them out:

```
git log <default branch ref>..HEAD --format='%h %s%n%b'
```

Every `Concern:` line goes under **Assumptions**, one bullet each, with the subject of the
commit it sits under.

**An empty Assumptions section is a claim.** It reads as "nothing was assumed". If it is empty because the context holding the answers is gone rather than because there were none, say that in one line instead of omitting the section.

**Check whether a preview link appeared** on the PR. If one did, put it first. If none appeared, give the local steps and do not mention a link that is not coming.

**The steps must be steps you actually ran.** Instructions you never followed will be wrong.

## 9. Hand off, then stop

**Never merge.** Opening the PR is where this skill ends.

The PR now exists, so the two built-in reviews finally have something to run against. Both are slash commands — **only the human can type one**, which is exactly why they sit here and not inside the automatic path. Offer them in one line, with the real PR number:

```
→ **opinion** /code-review 12, /security-review — yours to type, if installed
/security-review: this change touched database migrations
```

**Work the danger list out from the diff, not from memory.** Read the diff against the list in `flow` and decide again.

Name `/security-review` only when the change actually touched the danger list. Never report either as run, and never write their findings into the PR body — you have not seen any.

If a check goes red on the PR after this, or a reviewer asks for something, that is `devflow:tend` — it works out whose failure it is before anything gets pushed, and comes back through here so the same PR is updated.

Never suggest throwing work away. If discarding a branch or force-pushing genuinely comes up, the human must type the word `discard` — "sure", "ok" and "go ahead" do not count.

**Then what changed**, in one to three `done` lines — what this branch now does, in
words a user of it would know, not the file list:

```
✓ **done** build prints red and green as their own lines
```

It goes right above the recap, and the recap leaves it out.

**Then the recap.** Before the PR link, repeat the lines this run printed — from the first, `flow`'s or `build`'s when they ran before you, through this one — in the order they were printed, in one block. Leave out the routine ones, whose result is the same on almost every run: `– **pr** none found`, `✓ **branch**`, a green `✓ **checks**`, `✓ **debug** none found`, `– **look** nothing changed`, `✓ **handback**`. Every `✗` and `→` line stays. Add nothing to it — no summary, no new line, nothing this run has not already said once. It is the one place a human can read the whole run without scrolling back through the tool output sitting between the steps.

Then, as the last thing this skill prints, the PR's link:

```
https://github.com/<owner>/<repo>/pull/14
```

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never say "done", "fixed" or "passing" without output on screen proving it.
- Never leave step 6 silent. The `docs` line goes on screen either way, because
  "nothing was stale" and "I skipped it" look identical without it.
- Never claim a review ran when it did not. A slash command you cannot type has not run.
- Never assert that a skill, command or CLI exists. Check, then fall back, then say which you used. `/code-review` was asserted once and could not run; `run` and `gh` are the same shape.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never commit on the default branch.
- Never open a second pull request for a branch that already has one open.
- Never open a PR when the live check failed.
- Never invent check commands the project did not give you.
- Never merge, and never call `devflow:ship`. The open PR is where this skill ends.
