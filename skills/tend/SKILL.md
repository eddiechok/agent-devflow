---
name: tend
description: "Use when a pull request is already open and something about it needs attention - a check went red, or a reviewer left comments. Works out what the PR is reporting and whether this branch caused it, before changing anything. Fixes through build and re-submits, so the same PR is updated rather than a second one opened. Never merges; that is ship, and only a human starts it."
argument-hint: "[PR number, or blank for the current branch]"
allowed-tools: Bash(git status:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(git log:*), Bash(gh pr view:*)
---

# tend

Find out what the pull request is telling you. Decide whose problem it is. Then fix it.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- PR: !`if command -v gh >/dev/null 2>&1; then gh pr view --json number,title,state --jq '"#\(.number) \(.title) [\(.state)]"' 2>/dev/null || echo "none for this branch"; else echo "no gh here — look the PR up another way"; fi`

**`gh` is the example, not the requirement.** Every command below names *what to ask for*, not *how to ask*. Use whatever GitHub access this environment has — the CLI, an MCP server, the API. `no gh here` is not `none for this branch`.

## 1. Find the PR

`$ARGUMENTS` is a PR number if you were given one. Otherwise take the PR for the current branch.

**No PR → stop.** Say in one line that there is nothing to tend yet and that `devflow:submit` comes first. Check that is really what you are looking at: a missing CLI is not a missing pull request.

**No GitHub access at all → stop.** Say so plainly. Everything this skill does starts with reading what the PR reports, and a fix aimed at a failure you never read is a guess.

## 2. Read what it is reporting

```
gh pr view <n> --json state,mergeable,statusCheckRollup,reviewDecision,url
```

Then the detail behind each red check, and each open review thread. List what you found before doing anything:

```
#12  three checks, one red
  - lint       pass
  - test       FAIL  src/settings.test.ts, 2 cases
  - deploy     pass
  reviews: 1 changes-requested (2 threads open)
```

## 3. Triage before you touch anything

This is the step that earns the skill. For each item, one of three:

**Yours.** The failure is in code this branch changed, or in something it broke. A reviewer asked for something. Fix it.

**Not yours.** The check is red on the default branch too, or it names a service this diff never touches. **Do not push a change for it.** Say what is failing and why it is not this branch's, and leave it. Widening the PR to fix somebody else's breakage buries the change you are trying to land.

**Cannot tell.** Say what you would need to decide, and ask. A guess here costs a push, a CI run, and the reviewer's attention.

**"Flaky" is not a verdict.** It is what you say after you checked. Re-run a job only when it died before any test body ran — checkout, install, a runner that vanished — or when the same commit passed it earlier. Once, and only if you can. A second failure is real.

## 4. Fix it, one item at a time

Through `devflow:build`, which means the same five gates as any other change: the failing case becomes a test, you watch it fail for the right reason, then you make it pass. A CI failure is a bug report with a reproduction already attached, which is the easiest kind of test to write.

**Two rounds on the same failure, then stop.** Say what each attempt ruled out and hand it back. Three pushes at one red check is the same signal as three patches at one bug: the problem is somewhere other than where you are looking.

**Count across runs, not within one.** Nothing about this skill survives the session, and a red check is exactly the thing you get invoked at three separate times. Before the first fix, read what is already there:

```
git log <default branch ref>..HEAD --oneline
```

A commit that already names this failure means someone has been here — most likely you, in an earlier run. It counts. Two rounds is two across all of them, and the third time the useful answer is what has been ruled out, not another attempt.

Never get to green by weakening the thing that caught you. Deleting, skipping or loosening a test to make a check pass is on the danger list, and it is the one change here that is worse than leaving the PR red.

## 5. Re-submit

Call `devflow:submit`. It re-runs the checks fresh, runs the app, reviews again, and **updates the open PR** rather than opening a second one.

Do not push from here yourself. `submit` owns that, and skipping it skips the checks and the review that make the push worth trusting.

## 6. Answer the people

A reviewer who asked a question is owed an answer, not just a commit.

- **Done** — say so on the thread, with what changed.
- **Not doing it** — say why, in one line, on the thread. A silent refusal reads as a miss.
- **A finding you think is wrong** — check it against the code first, then say so with the technical reason. Never reject one you have not checked.

Then report, short: what was yours, what was not, what you pushed, what is still open.

## Rules

- Never merge, and never call `devflow:ship`. Merging is the human's.
- Never push a fix for a failure you have not attributed. Triage first.
- Never delete, skip or weaken a test to turn a check green.
- Never re-run a job hoping for a different answer. Once, for a reason you can name.
- Never push an empty commit, and never close and reopen a PR, to make CI start again.
- Never rewrite history on a branch that is not yours. No rebase, no amend, no force-push.
- Never open a second pull request. `submit` updates the one that is open.
- Never report a check as passing without the output that says so.
