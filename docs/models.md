# models, in detail

Why `models` is what it is. The steps themselves are in
[the skill](../.claude/skills/models/SKILL.md), the bookmarked pages are in
[its sources list](../.claude/skills/models/references/sources.md), and where each idea came from
is in [provenance](provenance.md).

`models` compares the `model:` and `effort:` pin in each `agents/*.md`, and the main
session's `model` and `effortLevel` in `~/.claude/settings.json`, with a short list of
pages. It shows one table and edits after one go.

## Why the pages decide

Every pin was set once, with a recorded reason, and new models ship after that. A pin
written against last quarter's models goes stale without anything failing: the agent still
runs, only on a worse or dearer setting than it needs. So the skill reads the benchmark and
docs pages again and proposes the change.

The pages decide, and not a number the skill makes up. Those pages are what a
person would check by hand: Anthropic's own matrix for which model, its cost and effort
pages for which effort, and a benchmark ranking as a second view. Where the pages do not
cover an agent's job, the agent keeps its setting and the table says why. The review
agents follow the pages too: Anthropic's matrix has no code-review row, so they read the
review page in the sources first, then the coding pages, and the three ranked review axes
move as one pair ([docs/review.md](review.md)).

The pages do not settle everything, and the human corrects in real sessions. A pin that is
a human's call, like the builder's sonnet pin on cost in [provenance](provenance.md), shows
up in the table with that reason, so the human sees what the page change would undo.

GSD works the other way: it has fixed model profiles (quality, balanced, budget and
inherit) that a person switches by hand, and it does not check any leaderboard
([get-shit-done](https://github.com/gsd-build/get-shit-done/)). `models` keeps a person's
go, and adds the pages to look at before it.

## Why one go

`models` edits files that outlast the session: the agent files go out in a PR, and
`~/.claude/settings.json` changes every later session on this machine. So it asks before
the first edit. It asks once, because a go row by row is a long wait for what is one
decision.

The ask is one table, in one reply: the agent or the main session, what it is now, what it
would become, why, and a URL for every number. Where two pages disagree, the row says so.
The human can then drop a row and say go, and every remaining edit is made at once. A
number with no URL cannot be checked, so it does not go in the table.

`models` carries `disable-model-invocation: true`, as `dispatch` and `sweep` do, so only
a human starts it. The project's own review agents in `.claude/agents/` are not touched,
because devflow does not own them ([docs/review.md](review.md)).

## Why no test runs

There is no eval case for `models`, and `models` runs no test on a setting it changes. That
is the human's call, on 12 Nov 2026: small tests are not meaningful for a model or an effort
setting. A handful of runs on one task would say little about whether a model is better at
review or at building, and a real eval across the agents would cost real money for a result
the pages already give. So the pages decide, and the human corrects in real sessions when a
setting turns out wrong.

The skill's own words are still pinned in `skills/test-frontmatter.py`: that it is hand
started, that it asks once before any edit, which keys it writes, and that every source is
an https link.

## Why the pages are read in the session

The pages are read in the session with `WebFetch` or `curl`, and not by researcher agents.
A researcher returns a summary, and a summary can garble a number: the Qodo post gives
different Sonnet 5.5 numbers in its text and in its table, and a summarizing fetch of the
cost page has to be read in three parts because it is about 217k characters. The table
puts a URL on every number so the human can check it, and that only works when the session
that writes the table has read the page itself.

The bookmark list is one file, `.claude/skills/models/references/sources.md`, so a new page is
one line, and a page that stops fitting is moved to its "Not fit now" list with the reason.

## Why it is not in the plugin

`models` lives in this repo's `.claude/skills/`, not in the plugin's `skills/`, so only this
repo loads it, as `/models`. A plugin loads its skills from `skills/` and nowhere else
([plugins reference](https://code.claude.com/docs/en/plugins-reference)), so a project that
installs devflow never sees it. That was the human's call, on 12 Nov 2026.

It is a tool for whoever maintains devflow, not for its users. The agent settings are the
plugin's own files: in another project, a plugin update writes over them, and users get new
settings when a release ships them. One person makes that call, in one place, as a PR.
The main session setting still reaches every project, because `~/.claude/settings.json` is
the user's own file and not the repo's.

## Why setup suggests a main-session pair

devflow pins every agent, but its own skills — `flow`, `plan`, `submit`, and every Quick and
Standard build — run in the main session, on whatever the user set with `/model` and
`/effort`. So `setup` prints one `→ **model**` line, once per project, with the pair to use,
and `README.md` carries the same pair. It is a hint and never an edit: the user's settings
change every project they work in, and that is their call. `/models` keeps the pair
current, in the same PR as the agent changes, so users get a new hint with the next release.
