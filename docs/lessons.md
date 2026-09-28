# Capturing lessons

The plan for [#57](https://github.com/eddiechok/agent-devflow/issues/57). **None of it is built.** The short version is in the [README](../README.md#what-is-not-here-yet).

The two-week rule still holds. Until about 2026-10-08, use devflow on the Mac. Use a web session only when you are away from the Mac, and start it with "use the devflow flow skill" ([docs/web.md](web.md) says why). Then decide from real data. If nothing went wrong, nothing here gets built.

## The goal

Improve all of devflow from real runs, not only `flow`'s sizing. Today the only piece is `~/.claude/devflow/overrides.md`, and it only collects ([docs/flow.md](flow.md)).

Collecting is the first step of a loop:

1. **Collect.** Log each mistake when it happens.
2. **Review.** Read the lessons together. Find the patterns.
3. **Fix.** Change the skill text.
4. **Check.** Turn the lesson into an eval case under `evals/`. Run the evals. The new case passes and the old cases still pass.

Step 4 makes each lesson a test that stays. The same mistake cannot come back without an eval failing.

**A human approves every skill change.** devflow never edits its own skills without one. One bad lesson, applied without a human, could quietly make every skill worse.

## Two kinds of lesson

| Kind | Example | Goes to | When |
|---|---|---|---|
| devflow | "`flow` sized a checkout change Quick. It was Deep." | the lessons repo | when it happens |
| project | "the tests need the sandbox key" | that repo's `CLAUDE.md` | at the end of `submit`, in the same PR |

The session that did the run sorts each lesson. It knows what went wrong. A fresh agent does not, so no subagent does this.

A project lesson goes in the PR, so the human sees it and approves it with the work.

## Where devflow lessons go

One line per lesson, in `lessons.md`, in a **private** repo: `eddiechok/devflow-lessons`.

```
2026-10-02 | shop-repo | build | wrote the test after the code
```

**Not in this repo's issues.** This repo is public. A lesson from a client project can name the client, a product or a bug. A leak cannot be fully undone.

**A file, not issues.** A web session has no `gh`, but it can push a file. One file also reads top to bottom at review time.

**One file for every project.** Lessons kept per project scatter, and a pattern only shows when you read them side by side. That is why `overrides.md` is global too.

`overrides.md` moves into this file. On a hosted session `~/.claude` is lost when the session ends, and the file with it.

## What writes a line

Only a mistake. A good run writes nothing.

- **By hand**, for any kind of mistake: `/devflow:lesson "..."`.
- **Automatically**, for the three clearest signs:
  - `flow`: the human used `--quick` or `--deep`. This exists today.
  - `review`: `hardcase` refutes a finding. The finding was a false alarm.
  - `ship`: Verify fails after the deploy.
- **Later**, only if the data asks for them:
  - the human stops `build`, or reverts what it wrote
  - `submit`'s checks pass, but CI fails
  - `tend` blames the wrong cause

## Reaching the lessons repo

Tested on 2026-09-25.

- **Mac:** the active `gh` account has write access to the repo. A push works.
- **Web:** by default a session reaches only the repo it was opened on, and it has no `gh`. A clone of a second repo fails with `could not read Username`. After the `add_repo` tool adds `eddiechok/devflow-lessons` to the session, `git push` to `main` works (probe commit `c03e36f`). `add_repo` showed the human no approval prompt.
- **Fallback:** if `add_repo` fails, the session prints the line in its reply, as `overrides.md` does today. The human copies it.

## The review step

A skill the human starts by hand, in a new session, for example once a month. It reads `lessons.md` and proposes skill changes, each with an eval case. It uses no subagents unless the file gets big.
