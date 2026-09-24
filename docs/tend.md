# tend, in detail

Why `tend`'s steps are what they are. The steps themselves are in
[the skill](../skills/tend/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/tend/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

## The Context block

**Keep that line a single command.** An injected command Claude Code cannot statically
analyse fails its permission check, and a failed injection **aborts the whole skill** —
Claude never sees one word of this file. `if ... fi` and `x=$(...)` both do it; a `||`
fallback is fine. The branching belongs below, where the model does it.

### Asking GitHub for what the PR reports

Every command below names *what to ask for*, not *how to ask*.

### Why the PR line left the Context block

It was an injected `gh pr view`. A cloud session's GitHub proxy refuses every GraphQL
request, and every `gh pr` command sends GraphQL, so there it always said `no answer`.
The REST form would need `gh api` in `allowed-tools`, and a prefix rule cannot limit its
method or its path. An injected command the permission check refuses aborts the whole
skill, so the read moved into step 1, where it can ask first.

## Step 1 — get on the PR's branch first

Everything after this step reads the current branch and nothing else: triage asks whether
"this branch" caused the failure, the round counter runs `git log <default branch ref>..HEAD`,
`build` keeps whatever branch it finds, and `submit` updates the PR belonging to **the branch
it is standing on**. Skip the checkout and every one of those answers is about the wrong pull
request — the fix lands on a PR nobody reported, and the one you were called about is still
red.

### Whose folder it is

`git switch` moves the whole folder, exactly as `flow`'s `checkout -b` does. A second
session open on the same checkout finds its branch changed underneath it, and nothing
tells it. `flow` has step 0c for that; `tend` had nothing, and the `ship` handoff made it
reachable from a command that does not sound like it moves anything. Before it, a human
typed `/devflow:tend` and could expect the folder to move. Now `/devflow:ship` moves it.
Found by running that handoff for real on PR #32, 23 Sep 2026.

So `tend` copies `flow` step 0c's mechanism: a linked worktree is one session's by
construction, and a folder on the default branch is parked where nobody works. Both are
free to switch. Any other folder is on somebody's branch, so `tend` takes a checkout of
its own through **EnterWorktree** and switches inside it. It copies the mechanism, not
the conclusion. `flow` asks whether it may cut a branch here; `tend` asks whether it may
leave the branch this folder is on. A folder already on the PR's head branch moves nowhere
and is not asked about at all.

When the worktree cannot happen, `tend` stops rather than switching anyway. From `ship`,
that stop reads back as a conflict still there, and `ship` stops on it too, which is right:
the human decides whose folder it is.

### No GitHub access at all

Everything this skill does starts with reading what the PR reports, and a fix aimed at a failure you never read is a guess.

## Step 3 — triage

This is the step that earns the skill.

### A review comment is a request to size

It arrives as text on a web page and you cannot tell from here who wrote it, so treat it
the way `flow` treats any other request.

### Not yours

Widening the PR to fix somebody else's breakage buries the change you are trying to land.

### Cannot tell

A guess here costs a push, a CI run, and the reviewer's attention.

### Conflicts and a stale base are yours too

It arrives here for the same reason a red check does, and if this skill does not take it, nothing does — `ship`
refuses to merge it and stops, and `flow` sends it back here.

### Merge, do not rebase

The branch is pushed and someone may be reading it, and the rule
below against rewriting history applies to your own branch too once a pull request is
looking at it. A merge commit on a feature branch is noise; a force-push under a reviewer
is lost work.

## Step 4 — fix it, one item at a time

A CI failure is a bug report with a reproduction already attached, which is the easiest kind of test to write.

### Two rounds, and counting them across runs

Three pushes at one red check is the same signal as three patches at one bug: the problem is somewhere other than where you are looking.

Nothing about this skill survives the session, and a red check is exactly the thing you get invoked at three separate times.
