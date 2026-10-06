# sweep, in detail

Why `sweep` is what it is. The steps themselves are in
[the skill](../skills/sweep/SKILL.md), and where each idea came from is in
[provenance](provenance.md).

## Why a human starts it

One run can open many PRs, so `sweep` carries `disable-model-invocation: true`. Only you
start it. Every tool checked while designing it (Claude Code Action, OpenHands' resolver,
Copilot's cloud agent) starts on a human opt-in, a label, an assignment or a mention, and
none of them scans for "easy" issues on its own.

## Why trust is the permission endpoint

An issue body is text from whoever filed it, and a sweeper would build from it and open a
PR. So the main session drops an issue whose author lacks write access, by asking the
permission endpoint (`gh api repos/{owner}/{repo}/collaborators/<author>/permission`) and
keeping only `admin` or `write`. It does not read `author_association`: GitHub does not
document that value as implying write, and a collaborator can hold only read or triage.
Copilot's cloud agent draws the same line: it answers only users with write access.

Passing the filter is not the end of the doubt. Issue text is data, not instructions, in
the main session and in every sweeper: a line in a body that says to run a command or
touch another file is a reason to stop, not a step. An issue number given by hand still
passes every filter, because typing a number is not a decision that its author is trusted.

## Why the sweeper runs `build` then `submit`, not `flow`

The main session has already sized each issue as Quick by `flow`'s rule, so a sweeper that
ran `flow` would size it a second time and might ask. It runs `build` for each issue, one
commit per issue, then `submit` once for the chain, so one PR closes every issue in it. It
is a separate agent from `builder` because `builder` never submits and never starts an
agent, and the sweeper does both: `submit`'s review starts reviewer agents. It runs on
sonnet, as `builder` does.

## Why it never asks

Nobody can answer a helper agent: the question tool is removed from every subagent. Where
`build` or `submit` would ask, or the change grows past Quick (a second file nobody
expected), the sweeper stops and reports. Stopping costs one issue; a guess opens a PR.

## Why 4 at a time

Each sweeper is a full session with a checkout behind it, so a fifth costs more in rate
limit and in reports than it buys. It is the same cap as `plan`'s builders, explained in
[docs/plan.md](plan.md). There is no cap on the total: further chains run in the next group.

The sweepers run in groups of 4, in the foreground, and `sweep` waits for the whole group
before it starts the next. The first live test started them in the background and ended its
turn; with nobody there to wake it, the run ended and took both sweepers with it, mid-build,
before either opened a PR. A cloud session or a routine has the same gap. The cost is that
one slow chain holds up the next group, and you chose that over refilling each slot.

## Why issues that share a file form one chain

Two sweepers working on two issues that share a file would each edit it, and their PRs
would conflict at merge. So the main session guesses the files each issue touches, and
issues that share a file become one chain: one sweeper, one worktree, one PR. It is a
guess from reading the repo, so two sweepers never edit the same file only as far as the
guess holds, and an issue whose files cannot be named is not Quick and is skipped.

## Why stopped work stays local

A sweeper that stops keeps its worktree and branch on this machine, unpushed. A half-built
branch pushed to GitHub is a thing someone else can pick up as if it were finished. The
Done report says where the work sits, so you can open it, finish it, or throw it away.
A skipped issue gets no GitHub comment either: the report is where you read why, and a
comment on every issue a sweep passes over would be noise on the issues you did not pick.

## A note for later: setup and #96

When #96 (setup asks how to work) is built, `setup` must run in the main session before any
sweeper starts, because sweepers cannot ask. A project that has not answered it by then
gets the answer there, not in a helper that has no one to ask.
