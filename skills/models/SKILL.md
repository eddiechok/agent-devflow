---
name: models
description: "Use to review which model and effort each devflow agent and the main session run on, against a short list of bookmarked benchmark and docs pages. Only a human starts it, because it edits agent files and ~/.claude/settings.json. Reads the pages in the session, shows one table of now, new and why with a URL for every number, waits for one go, then makes every edit. Agent changes go out as a PR through devflow:flow."
argument-hint: ""
disable-model-invocation: true
---

# models

Read the pages. Show one table. Edit only after one go.

Why it is built this way: [docs/models.md](../../docs/models.md). Read it only if a rule
looks wrong.

## What this is

Each devflow agent pins `model:` and `effort:` in `agents/*.md`, and the main session's
defaults are the `model` and `effortLevel` keys in `~/.claude/settings.json`. Both go stale
as new models ship. This skill compares them against the pages in
[references/sources.md](references/sources.md) and proposes the change.

**It reads the pages, then asks once.** No test runs a setting: the pages decide, and the
human corrects it in real sessions.

**The agent edits need the agent-devflow checkout.** Editing `agents/*.md` only makes sense
there, and the plugin is on in other projects too. Steps 1 to 3 only read, and
`~/.claude/settings.json` is the human's own file, so they work from any folder. Before
step 4's agent edits, check that `agents/` and `skills/test-frontmatter.py` exist in this
folder. If they do not, still offer the settings.json rows, say this is not the
agent-devflow checkout, and stop before editing any agent.

## 1. Read what is set now

Read `model:` and `effort:` from the top of each file in `agents/`, and `model` and
`effortLevel` from `~/.claude/settings.json`. The installed plugin carries `agents/` and
`docs/provenance.md` beside this skill, so read them from this skill's own directory
anywhere. Read the recorded reason for each pin in `docs/provenance.md`, because a reason
that was a human's call is not undone by a benchmark alone: say it in the row.

The project's own review agents in `.claude/agents/` are not devflow's. Leave them alone.

## 2. Read the pages

Read every page in [references/sources.md](references/sources.md) in this session with
`WebFetch` or `curl`, never through a researcher agent. Quote each number with its URL. A
summarizing fetch can garble a number, so where two places on a page disagree, or one page
disagrees with another, write that in the table instead of picking one.

## 3. Show one table

One table, one reply. A row for each agent and one for the main session:

| agent or session | now | new | why | URL for every number |
|---|---|---|---|---|

- **Now** and **new** are `model / effort`. A row with nothing to change says `keep`.
- **Why** is in words a human can check against the page. Where the pages disagree, say so
  in the row.
- **Where the pages do not cover an agent's job**, that agent keeps its setting, and the row
  says why. A review has no row in Anthropic's matrix, for one.
- An agent must pin both `model:` and `effort:`. `inherit` is not a pin.

Then ask once: go, or change which rows. This is the one go before any edit. Do not edit a
file before it, and do not ask again row by row.

## 4. Make every edit

On the go, edit every row the human left in, and nothing else.

- **Main session:** set `model` and `effortLevel` in `~/.claude/settings.json`. Change only
  those two keys.
- **Agents:** change the `model:` and `effort:` lines of `agents/*.md`. These go out as a
  PR, so hand them to `devflow:flow` with the table as the request. Do not commit them here.

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never edit a file before the one go on the table.
- Never touch `.claude/agents/`; devflow does not own those agents.
- Never change an agent the pages do not cover; it keeps its setting.
- Never report a number without its URL, or hide a place where the pages disagree.
- Never read the pages through a researcher agent.
- Never commit an agent change here; `devflow:flow` opens the PR.
