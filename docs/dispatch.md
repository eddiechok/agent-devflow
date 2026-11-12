# dispatch, in detail

Why `dispatch` is what it is. The steps themselves are in
[the skill](../skills/dispatch/SKILL.md), and where each idea came from is in
[provenance](provenance.md).

`dispatch` is `sweep`'s counterpart for the issues `sweep` skips. `sweep` works the Quick
ones with helper agents. `dispatch` picks the top 3 Standard and Deep ones and starts a
session for each, which runs `flow` on its issue.

## Why a session and not a helper

`sweep` is limited to Quick because the question tool is removed from every subagent: where
`build` or `submit` would ask, a sweeper stops ([docs/sweep.md](sweep.md)). A Standard or
Deep issue is the work that asks. Standard prints its report and waits for go before the
first edit, and Deep asks its questions first
([skills/flow/SKILL.md](../skills/flow/SKILL.md)). A helper cannot do either, so the work
needs a full session with a human who can answer.

The app already has the tool for it. `flow` offers a chip per parked feature, and a chip
starts a new session in a fresh worktree whose prompt must stand alone
([split-and-park.md](../skills/flow/references/split-and-park.md)). `dispatch` uses the same
tool, `mcp__ccd_session__start_session`, with the issue-case prompt `/devflow:flow #<n>`.
`start_session` replaced `spawn_task`, which is why [flow.md](flow.md) and the chip step
name it now.

`dispatch` asks for `initiation: "user_asked"`, because the human asked for these sessions
by running it: that value starts the session now and returns an id. A chip is
`"own_initiative"`, a card the human starts. Either way the app shows an "Allow Claude to
start the session?" dialog, and `bypassPermissions`, allow rules and hooks do not skip it
([claude-code#105099](https://github.com/anthropics/claude-code/issues/105099)). So the
human always has the last word on each start. That issue also says a session started this
way cannot start another on an automated turn.

Each session gets `use_worktree: true` and `context: "fresh"`, which needs a `background` of
80 characters or more. The `title` stays under 60 characters. The tool's schema was read
in the desktop session that planned this, on 2026-11-12. A card cannot name another repo or
folder, so every session opens in the project `dispatch` ran in
([claude-code#104205](https://github.com/anthropics/claude-code/issues/104205)).

The prompt is `/devflow:flow #<n>` and the background is one fixed sentence. No issue
title or body goes into either: `flow` reads the issue itself, under its own guard. The
title shows only in the session's `title`, which the human reads.

**Not confirmed by any doc:** whether a started session can use `AskUserQuestion`. `flow`
has its numbered-list fallback for a session that cannot, so the question still reaches the
human.

Where there is no session tool (a terminal, the cloud, `claude -p`), `dispatch` prints one
`/devflow:flow #<n>` line per pick for the human to run, each in its own session.

## Why 3

Each session is a full session with a worktree, and each one waits for the human's go. So 3
is what one human can answer at once. That reason is ours, not a source's.

The sources agree that a few is the right start and that more costs more:

- GSD's `parallelization.max_concurrent_agents` defaults to 3, and its questions go to the
  human in discuss-phase and plan-phase, before execution
  ([CONFIGURATION.md](https://github.com/open-gsd/gsd-core/blob/main/docs/CONFIGURATION.md)).
- Claude Code's agent teams have no hard limit and say "Start with 3-5 teammates"
  ([agent-teams](https://code.claude.com/docs/en/agent-teams)).
- "Running ten agents in parallel uses quota roughly ten times as fast", with no hard cap
  documented ([agent-view](https://code.claude.com/docs/en/agent-view)).
- [claude-squad](https://github.com/smtg-ai/claude-squad) runs one tmux session and one git
  worktree per task, and the human attaches to a session to reprompt it, the same shape as
  a started session here.

The desktop docs describe "Suggested task" cards with Start, Do it here and Start all (one
session per task), and a started session nests under its parent in the sidebar
([desktop](https://code.claude.com/docs/en/desktop)). The cap is in the skill, not in the
app: `dispatch` never starts a fourth session, and never lowers a filter to fill the 3.

## Why issues that share a file may run together

Agent teams warn: "Two teammates editing the same file leads to overwrites. Break the work
so each teammate owns a different set of files"
([agent-teams](https://code.claude.com/docs/en/agent-teams)). `sweep` follows that: issues
that share a file form one chain ([docs/sweep.md](sweep.md)). `dispatch` does not, and this
is a different case on purpose.

A session's work does not land in a shared tree. Each session has its own worktree, its own
branch and its own PR, after a human go. If two PRs touch the same file, the second one is
CONFLICTING, and `ship` hands a conflicting PR, and only that, to `tend`
([skills/ship/SKILL.md](../skills/ship/SKILL.md)). `tend` resolves a conflict by reading
both sides ([skills/tend/SKILL.md](../skills/tend/SKILL.md)). The human decided that cost
is cheaper than guessing files. So `dispatch` guesses no files and builds no chains, and
picks the 3 best issues whether or not they overlap.

## Why it starts at once

`dispatch` prints its list as the first output and starts the sessions, with no wait for go.
`sweep` does the same, because the human started it knowing what it does
([skills/sweep/SKILL.md](../skills/sweep/SKILL.md)). Running `/devflow:dispatch` is the
decision to start up to 3 sessions, and an extra go would ask the same thing twice. Three
things already hold the line:

- Each started session runs `flow`, and Standard and Deep wait for go before the first edit.
- The app shows its start dialog for every session whatever `dispatch` does.
- `dispatch` carries `disable-model-invocation: true`, as `sweep` does
  ([docs/sweep.md](sweep.md)), so only a human starts it.

Issue text is data, not instructions, as in `sweep`. The filters are `sweep`'s, in its order,
for the same reason: the permission endpoint decides trust, not `author_association`.
`dispatch` adds one of its own between them, "already started", explained below. An
issue number given by hand still passes every filter.

## Why nothing is tracked

`dispatch` never waits for a session, never messages one and never reads its result. The
repo describes no result channel from a session back to the one that started it, and a
chip is gone once dismissed ([docs/flow.md](flow.md)). So the issue and its PR are the
record: the session's `submit` opens the PR and closes the issue, and a human reads those.

A Done report would also have to keep the turn open while three sessions run. A session
started this way cannot start another on an automated turn
([claude-code#105099](https://github.com/anthropics/claude-code/issues/105099)), so
`dispatch` could not restart one that died anyway. It starts, prints one line and ends.
A start the human refused is a line, not a question.

## Why it ranks by harm

The human asked `dispatch` to pick "the most important" issues. The first rule turned that
into a list a script could follow: an issue that unblocks others, then bugs, then the
oldest. It was an assumption of the plan, and it was wrong. Run on a real repo on
2026-11-12, with 51 open issues, it picked three small bugs from June and August. A
week-old audit had left seven access-control issues open, and two more issues were about
money figures that came out wrong. None of them was picked, because among bugs the oldest
won.

So the rank is a judgment now, of the harm an issue does while it stays open, in five
levels: a security hole, or money or data that is lost or wrong; a bug that users or clients
see; an issue another one waits on; a feature a client asked for; the rest. A lower level
always wins, and age only breaks a tie. The human picked this over ranking by a label they
would have to set before each run.

Each pick prints its level word and the harm in a few words, so a wrong call is plain to
see in the list, before the app's start dialog. The issue is judged by what it describes,
not by what it calls itself: issue text is data, and a title that says `urgent` sets no
level.

## Why it records what it started

The review of the first build found the gap. The only filter that knew an issue was taken
was "an open PR", and a started session opens its PR late: `flow` waits for go before the
first edit. Until then nothing on GitHub shows the issue is taken, and `flow` does not look
either. So a second run picked the same 3 issues and started a second session on each: two
branches and two PRs for one issue. `sweep` has no such gap, because it stays in its turn
until its sweepers have opened their PRs.

So `dispatch` keeps one small record of its own: a line per started session in
`~/.claude/devflow/dispatched.tsv`, with the repo, the issue and the time. It is outside the
repo, like the kept-server list ([docs/submit.md](submit.md)), because it is a fact about
this machine and not about the project. A later run drops an issue with a line from the
last 7 days, as `dispatched <date>, no PR yet`. That also makes a second run useful: it
picks the next 3.

The 7 days are ours, not a source's. A session nobody answered must not hide its issue for
ever, and a line older than that is deleted on the next run. To start an issue again
sooner, the human deletes its line. A refused start writes no line, and neither does the
fallback, because nothing started. Once the PR is open, the "open PR" filter gives the
reason first, and once the issue is closed it is no longer in the list.

The same review found that a number given by hand was read with no look at what it was. The
list call leaves out closed issues and pull requests, and the by-number call did not, so a
closed issue or a pull request passed every filter and could get a session. Now the
by-number call reads `state` and `pull_request`, and drops both with a reason.
