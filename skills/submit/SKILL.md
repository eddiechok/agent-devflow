---
name: submit
description: Use when the code is finished and ready to become a pull request. Runs the project checks fresh, runs the app to confirm the change really works, writes a conventional commit, and opens a PR with steps for the human to check it. Never merges; merging is what the ship skill does, and only a human starts that.
argument-hint: "[tracker: one issue action per line, before the request] [request: the words the human typed, passed on to review as the spec] [start: <sha>, size: <Quick|Standard|Deep>, mode: pr - from flow]"
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

**Direct mode** — `Mode: direct` in the `## Workflow` block of `CLAUDE.md` and no `mode: pr`
line — is not this skill as written below. Read [references/direct.md](references/direct.md)
now: it says what changes at steps 1, 5, 7 and 8. Every other step runs as written.

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

Only skip when there is genuinely nothing to exercise — a library with no entry point, a pure refactor with no observable change. Print `– **live** nothing to exercise — <reason>`. Do not invent a fake check, and do not call a passing test suite a live check; step 2 already ran that.

Otherwise read [references/live-check.md](references/live-check.md) and follow it: how to launch or run the change, what counts as proof, and what to do when it does not work.

## 5. Review the change

In direct mode, review follows `size:` and the fixed point is `start:`: [references/direct.md](references/direct.md).

Invoke `devflow:review` with the branch point:

```
git merge-base HEAD <default branch ref>
```

**Pass it the request text too, if you were given one.** `flow` hands it over at its step 5 as `request: <text>`, word for word; hand it to `review` in the same form, after the fixed point. If you were invoked directly and have no request, say so in one line and let the axis skip — do not write one from memory of the diff.

**Pass `no-behaviour: <reason>` too, when `build` said there was nothing to test.** `build` has one gate for that, and it prints `– **no-behaviour** <reason> — running the checks instead`. Hand that reason on **as its own line**, `no-behaviour: <reason>`, after the fixed point and the request — `review` recognises it only at a line start. `review` then runs `reviewer` alone, to check the words still match the repo, and reports **Challenged**, **Security** and **Right thing** as `skipped — no behaviour`. Act on its findings like any others below; the skipped sections are nothing to fix. Under **Evidence** at step 8 write `Review: reviewer only, no behaviour`.

Only `build` decides this, and only for the change in front of it. If `build` ran the gates, the axes run — never reach for the exit yourself because the diff looks small or because it is all markdown.

Do not do the review here — a session reviewing the code it just wrote carries every assumption that produced it.

Then act on what comes back. **A finding, an axis `NOT RUN`, or a `Not reported:` line** → read [references/findings.md](references/findings.md) first: what to fix, what you may reject, and how round 2 runs. A clean report has nothing to act on.

**The last read decides the security pass, not the first.** Before the commit, read the whole diff once more against the five security items — auth and permissions, secrets and keys, payments, public API or wire format, CI/CD config. It is a list to check, not a review. If one is touched and `security-reviewer` has not read the lines that touch it — it never ran, or they arrived after it did — start it on those lines, scoped like a round 2. A fix is the likeliest place for a permission check to arrive.

The review reports; it never edits. The fixes are yours. Once it is settled, print one line that names what was found:

```
✓ **review** 2 found, 2 fixed — a loose test scanner, a stop line with no mark
```

or, when `build` said there was nothing to test:

```
✓ **review** reviewer only, no behaviour — 0 found
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

**If this run learned a fact worth keeping** — about this project, or about devflow itself — read [references/lessons.md](references/lessons.md). Nothing learned → print nothing.

## 7. Commit

In direct mode the commit lands on main and is pushed, with the Assumptions in its body: [references/direct.md](references/direct.md). A linked worktree lands through [references/land-on-main.md](references/land-on-main.md).

**If any file changed since step 2's run, run the checks again first.** Same rule as step 2: the checks must postdate the last edit. Bare, one per call, output on screen.

**If any file changed since the last review that read it, one short look first.** Read [references/look.md](references/look.md) and follow it. When nothing changed, there is no look to run: print `– **look** nothing changed since the last review`.

**If anything is going under Known issues**, read [references/known-issues.md](references/known-issues.md) before the commit: it sorts them, and parks each leftover bug so its backlog item ships in this PR.

**A bug an earlier run parked, which this branch has since fixed**, comes out of Known issues on every run, clean or not: add `Closes #48` under **Why**, or delete its backlog file in this branch. A deleted backlog file is an edit: run the `## Checks` block again — bare, one per call — before the commit.

Conventional commits, so `git log` doubles as a changelog:

```
<type>(<scope>): <imperative subject>

<why this change, not what — the diff already says what>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`. `build` uses this same list for plan pieces; the two have to stay in step.

**A request with an `Also parked as` line** came from a `flow` chip — read [references/backlog-chip.md](references/backlog-chip.md).

**A Deep branch, or a `devflow:plan` issue** — read [references/plan-and-concerns.md](references/plan-and-concerns.md) now: it covers this commit and the PR body at step 8.

Otherwise, once the commit is in:

```
✓ **commit** feat(settings): read the flag in the API (a1b2c3d)
```

## 8. Open the PR — or update the one already there

In direct mode there is no PR: skip this step and put its body in the Done report ([references/direct.md](references/direct.md)).

**First, does this branch already have an open pull request?** Ask through whatever GitHub access this environment has. With `gh`, that is `gh api`, never the `gh pr` commands: those send GraphQL, and a cloud session's GitHub proxy refuses every GraphQL request.

```
gh api 'repos/{owner}/{repo}/pulls?head={owner}%3A<branch>&state=open' --jq '.[].number'
```

Write the PR body to a fresh file outside the repo — never a fixed path, which another
session or another user can reach first:

```
mktemp "${TMPDIR:-/tmp}/devflow-pr.XXXXXX"
```

The path it prints is `<body file>` below. Remove it once the PR has it.

**`flow` passed `tracker:` lines?** Read [references/tracker-actions.md](references/tracker-actions.md) before you write the body — it changes the body — and do the actions it lists once the PR is open.

**No PR** — push, then open one against the default branch:

```
gh api repos/{owner}/{repo}/pulls -f title="<subject>" -F body=@<body file> -f head=<branch> -f base=<default branch> --jq '"#\(.number) \(.html_url)"'
```

Then print:

```
✓ **pr** opened #14
```

**A PR already open** — push to the same branch, then update that PR, never a second one: read [references/update-pr.md](references/update-pr.md).

**Opening it is what you were asked for.** Invoking this skill *is* the request; it says so in its own description, and so does `flow`. Do not stop here to ask again.

If the environment blocks it anyway, push the branch and then give the human the compare link and the command for whatever access they have — the `gh api` call above, or the equivalent — in two lines. Never end silently on a pushed branch with no PR — work that is finished, green and invisible is the state this skill exists to prevent.

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
- Review: all three ran — is it built right, is it safe from an attacker, and is it the right thing, naming which were `NOT RUN` and which were `skipped` (or: security-reviewer skipped — no security item touched, right thing NOT RUN — no spec; or: reviewer only, no behaviour)

## Known issues
- (only if the review left something unresolved)
- step 7 of ship has no line for retargeted PRs — parked as #48
```

**An empty Assumptions section is a claim.** It reads as "nothing was assumed". If it is empty because the context holding the answers is gone rather than because there were none, say that in one line instead of omitting the section.

**Check whether a preview link appeared** on the PR. If one did, put it first. If none appeared, give the local steps and do not mention a link that is not coming.

**The steps must be steps you actually ran.** Instructions you never followed will be wrong.

## 9. Hand off, then stop

**Never merge.** Opening the PR is where this skill ends.

The PR now exists. Step 5 already ran the security review this repo runs — `security-reviewer`, whenever the danger list called for it, and `hardcase` against its findings the same as `reviewer`'s. There is nothing left to offer the human here.

If a check goes red on the PR after this, or a reviewer asks for something, that is `devflow:tend` — it works out whose failure it is before anything gets pushed, and comes back through here so the same PR is updated.

Never suggest throwing work away. If discarding a branch or force-pushing genuinely comes up, the human must type the word `discard` — "sure", "ok" and "go ahead" do not count.

**Then the Done report**, right before the PR link: the plan's rows, each marked done or
not, then what the user will see, the check steps, assumptions, tracker actions, and what
needs the human. Its shape is the Done section of
[flow's references/report.md](../flow/references/report.md). It is the one place a human can read the whole run without scrolling back
through the tool output sitting between the steps.

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
- Never commit on the default branch in pr mode.
- Never open a second pull request for a branch that already has one open.
- Never end a pr-mode run without a pull request.
- Never open a PR when the live check failed.
- Never invent check commands the project did not give you.
- Never merge, and never call `devflow:ship`. The open PR is where this skill ends.
