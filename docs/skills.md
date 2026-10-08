# skills, in detail

Why `skills`' rules are what they are. The steps themselves are in
[the skill](../skills/skills/SKILL.md), and the short version is in the
[README](../README.md). The request was issue #91: a skill that finds agent skills that fit
this repo.

## Why it lists and never installs

An install runs someone else's text in every later session: a skill is a prompt, a plugin may
carry hooks and an MCP server. That is a decision for the person who owns the repo, so the
skill never installs. It prints the exact command and the human runs it, and decides which
ones. This is find-skills' own step, "show the command, don't install", copied with credit
(see [provenance](provenance.md#skills)).

The commands are at project scope (`--scope project`, which writes the committed
`.claude/settings.json`), because the repo is what the suggestion fits. A committed entry
turns the plugin on for collaborators but does not download it, so the list says that each
person still runs the install once. Cloud sessions do not load project-scope plugins at all.

## Why it reads what is installed first

Suggesting what is already there is noise, and two copies of one thing is a fault. So the
skill reads `claude plugin list --json`, `claude mcp list` and the loose `SKILL.md` folders
(neither CLI command sees loose skills) before it suggests anything. All three only read.

## Why a table, then a search

The vendor table is small on purpose: Railway, Medusa, Cloudflare, Supabase, Stripe. A row
fires on a file signal and on nothing else, and every row is an official vendor repo or has
1k+ stars, so the table can be trusted without a search. What the table misses goes to
`DISABLE_TELEMETRY=1 npx skills find <query>`. The variable keeps the search from sending
anonymous usage data. When npx is missing the fallback is skipped and a line says so, so a
gap in the list is never read as "nothing exists". A big vendor list would go stale and is
out of scope.

## Why design and UX skills get a live search too

The first version took design skills from the table alone. A table goes stale: stars move,
a skill is renamed, and a better one appears. So for design and UX skills the skill runs a
live search every run on top of the tables, and reads stars and size fresh for every skill
it lists, table rows included, so the number printed is the number that day (#108). A new
find that passes the source bar may be recommended over a table row, with the reason in one
line, but the list still holds one design skill and one UX skill. The search is fuzzy and
prints install counts, not stars or a description, so a result is only a lead until the
bar has been applied to it.

## Why it searches only what the repo is built with

A search for "testing" or "code review" finds skills that compete with `build` and `review`.
devflow owns how work is done: code quality and review, the testing process and TDD,
productivity, workflow and git. So the skill searches only what the repo is built with: the
web framework, the test tools, the deploy target, an API-docs skill only when an openapi
file exists, and a review agent for that stack. A review agent for the stack checks rules
`review`'s own agents do not know, so it adds to `review` rather than competing (#136).

## Why a repo with code is never asked a stack question

The files already say what the stack is, so asking is asking for a fact. A missing deploy file
means there is no deploy to suggest for, which is a reason to skip it, not to ask. An empty
repo is the one case with nothing to read, so it gets up to 4 stack questions together
(frontend, backend, database, deploy), each with "Not decided yet" as the recommended answer,
and a line to run it again once code exists. Files win over answers: the answers only stand
in until a file says otherwise.

## Why one design skill

The design generators (`frontend-design`, `taste-skill`, `impeccable`, `ui-ux-pro-max`,
`minimalist-skill`) each give a style directive, and installed together the directions are
competing. `minimalist-skill` conflicts with `frontend-design`'s bold direction outright. So
the list holds one design skill, picked by up to 3 questions asked together (what the UI is for,
what look, new or improve), plus `web-design-guidelines`, which only reviews and clashes with
nothing. The facts are read first, so each question has a recommended answer from the repo.
When several design skills are already installed the skill warns and names them, and when the
pick sits at user scope only it prints the commands to move it to project scope. Those
commands are printed and never run, because one of them deletes a folder.

## Why one UX skill

A design skill says how the UI looks. Nothing in the list said whether it works, and the
look question in `flow` (#108) needs something to check its variants with. So a repo with
a UI also gets one UX skill, picked from the same answer to "what is the UI for?" and the
same repo facts, with no new question: web screens and landing pages take the Anthropic
design plugin, a React Native or Expo app takes wondelai's `ux-design`. Both set no style,
so they clash with neither the design pick nor each other, and still the list holds one,
because two critiques of the same screen overlap.

`impeccable` is the exception. It carries a `critique` command that scores Nielsen's 10
heuristics, so suggesting a UX skill beside it would pay twice for one review. The list says
`/impeccable critique` is the check and suggests nothing else.

## Why the source bar

A search result is not a recommendation. Official vendor repo, or 1k+ stars; under 100 stars
is a reason to drop it. These are find-skills' quality rules, copied with credit. The star
count follows the repo's own rule in [provenance](provenance.md): copied text is always
credited, and a count is a reason to list something, never a reason to trust it blind.

## Why a collection is judged by install count, and 100 to 999 stars is one line

Stars belong to the repo, and a repo with 10 or more skills (wondelai/skills holds 65) has
stars from the whole collection, so they say little about the one skill in it. The install
count is per skill, so that skill is judged by its own, 1K+. Smaller repos still use stars.

A repo of 100 to 999 stars was undefined before: not trusted enough to suggest, not small
enough to drop. It is never suggested, and it is not hidden either: one "Also seen" line at
the end names it with its stars and no install command, so the human knows it exists and can
look. Under 100 stars stays dropped, because a line for every stray repo would be noise.

## Why each entry says what it carries and its size

A plugin can be one skill or hooks, an MCP server and scripts. The human is about to put it in
the repo for everyone, so the list says which, and how big. A plugin that carries an MCP
server is never listed together with its MCP-only install, since the plugin already has it.

## Why it is model-invocable and does not touch setup

The skill has no `disable-model-invocation`, so the model can start it. `setup` calls it
as its last question (issue #96), and you can start it by hand, as `/devflow:skills`.

## Why it finds review agents and writes one line

A project can have its own review agent in `.claude/agents/`. bykare-medusa-admin's
`medusa-convention-reviewer` checks its Medusa v2 and React rules: money math, RBAC,
logging, table filtering. `review` never ran it, so those checks were lost. Issue #136
gave each step one owner: `skills` finds the agents, the human chooses per agent, the
choice is one `- Review agent:` line in `## Workflow`, and `review` runs only what the
lines name.

`skills` finds them because it already reads what is installed, and an agent file is one
more thing installed. It picks by `description`, since that is what the agent says it is
for.

It writes the line itself, after a yes for that agent, and nothing else. An install is
someone else's text running in every session, so the human runs it. One line naming an
agent the repo already has is not that: the human said yes to that line in that moment,
and pasting it by hand would be one more step for the same result. The line goes in
`## Workflow` because that block already holds devflow's settings for this project.

It recommends No for an agent whose `tools` can edit. A review reads; one that changes the
code it reads is not a review, whatever its description says.

## Not in scope

Removing old skills when the stack changes, and a big vendor list.
