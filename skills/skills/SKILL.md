---
name: skills
description: "Use when the human asks which agent skills, plugins or MCP servers would suit this project, or when setup wants to offer them. Reads the repo's files for what it is built with, reads what is already installed, then suggests skills that fit, each with why, what it carries and its size, and the exact install command. Lists only: the human runs every install."
---

# skills

Look at what this repo is built with. Suggest the skills that fit it. Print the install
command for each, and stop: the human runs it.

Why these rules are what they are: [docs/skills.md](../../docs/skills.md). Read it only if a
rule looks wrong.

## 1. Read what is already installed

Before suggesting anything, read, one command per call:

- `claude plugin list --json`: installed plugins, with scope and enabled status
- `claude mcp list`: MCP servers, including ones a plugin carries
- the loose skills: `.claude/skills/*/SKILL.md` and `~/.claude/skills/*/SKILL.md`

Both CLI commands only read. A suggestion that matches something already installed is
dropped, with one line saying it is already installed, and a suggestion that would clash with
an installed one gets a warning line instead of a silent second copy.

## 2. Read the repo

Look at the files, not at what the README says:

- the manifest: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`,
  `composer.json`, and the like. Read the dependency names.
- deploy files: `railway.json`, `railway.toml`, `wrangler.jsonc`, `wrangler.toml`,
  `Dockerfile`
- `supabase/`, `playwright.config.*`, and any `openapi.*` or `swagger.*` file
- what the `## Checks` block in `CLAUDE.md` runs, when there is one

**An empty repo** has no manifest and no source files. Ask up to 4 stack questions in one
round: frontend, backend, database, deploy. Each question's recommended answer is "Not decided
yet", and the round never asks for more than the four. Then print one line saying to run it
again once there is code. Files win over answers: when the repo has a signal, the file decides
and the answer is ignored.

**A repo with code** never gets a stack question. The files answer them. A missing deploy
file means skip deploy, not ask what the deploy is.

## 3. Match

Look each signal up in [the vendor table](references/vendors.md). A row fires on its file
signal and on nothing else.

Then go through what the table missed, and search only what the repo is built with: its web
framework, its test tools, its deploy target, and an API-docs skill only when an openapi file
exists. Never search how-to-work categories, because devflow owns them: code quality and
review, the testing process and TDD, productivity, workflow and git.

For each such search, run `DISABLE_TELEMETRY=1 npx skills find <query>`. The variable keeps
the search from sending anonymous usage data. When npx is missing, skip the fallback and
print a line saying so, so a gap in the list is never read as "nothing exists".

## 3a. A repo with a UI

Read the frontend facts first: `react-native`, `expo`, `electron` or `tauri` in the
dependencies, a `tailwind.config.*` file, a `components/ui` folder, and how much UI code
there is. No UI at all means skip this step.

Then ask up to 3 questions in one round: what the UI is for, what look it should have, and
whether it is new or an improvement (only when UI exists). Each has a recommended answer
taken from the facts. The questions, and which skill each answer points at, are in
[the design reference](references/design.md).

Suggest **one design skill** and nothing else that generates a style, plus
`web-design-guidelines`, which is review-only and clashes with nothing. Design skills give
competing directions when installed together, so two of them is never a list.

For design and UX skills, run `DISABLE_TELEMETRY=1 npx skills find <query>` every run, on top
of the two tables: a table is a reference that goes stale, and a better skill may exist. Read
stars (`gh api`) and size fresh for every skill that would be listed, table rows included,
never from the table. A new find that passes step 4 may be recommended over a table row, with the
reason in one line. The result is still one design skill and one UX skill.

Then suggest **one UX skill**, picked from the same answer to "what is the UI for?" and the
frontend facts, with no new question. It sets no style, so it clashes with nothing. When the
design pick is `impeccable`, which carries its own UX review, there is no UX skill and no
second one: say `/impeccable critique` is the check. The table and the pick are in
[the UX reference](references/ux.md).

When several design skills are already installed, print a clash warning naming them. When the
pick is installed at user scope only, print the commands to move it from user scope to
project scope. Never run them.

## 4. Check the source before listing it

Do not list a skill on the strength of a search result alone. A skill from the table has
already cleared the bar. For anything else:

1. Official sources first: the vendor's own repo, or a publisher the ecosystem knows.
2. The repo's stars: 1k+ stars, or an official vendor repo. 100 to 999 stars is never
   suggested; it goes on the one Also seen line in step 5. Anything under 100 stars is
   dropped, not mentioned.
3. Install count, where the search shows one. Prefer 1K+.
4. A repo with 10 or more skills is a big collection, and its stars say little about one
   skill in it. Judge that skill by its own install count (1K+), not the repo's stars.
   Smaller repos still use stars.

## 5. Print the list

One entry per suggestion, at most 1 or 2 for each part of the stack:

- the name, and why it fits, naming the file that triggered it
- what it **carries**: skill only, hooks, an MCP server, or scripts
- its **size**: how many skills it holds, and how many lines of markdown where that is cheap
  to read. Read the plugin's folder at run time with `gh api repos/<owner>/<repo>/contents/<path>`.
  Where `gh` cannot reach it, write "size not read" rather than a number you did not see.
- its **stars**, read fresh with `gh api repos/<owner>/<repo>`, or "stars not read" where
  `gh` cannot reach it; for a big collection (step 4), its install count instead
- the exact install command, at project scope

The commands, which the human runs:

```
claude plugin marketplace add <owner/repo> --scope project
claude plugin install <plugin>@<marketplace> --scope project
```

For a source installed with the skills CLI: `npx skills add <owner/repo>`. Project scope is
that command's default.

A committed project-scope entry turns a plugin on for everyone in the repo, and each person
still runs the install line once.

Put one line at the end of the list for what step 4 held back, with no install command, and
leave it off when nothing was held back:

```
Also seen, not suggested (small repos): <skill> (<owner/repo>, <stars> stars)
```

**Never suggest a plugin and its own MCP-only install both.** A plugin that carries an MCP
server already has it. Print the plugin and leave the MCP-only line out.

**Never run an install command.** Not `claude plugin install`, not `claude plugin marketplace
add`, not `npx skills add`, not `claude mcp add`. The list is the output; the human runs
each command, and decides which ones.

## Rules

- Never run an install command. Print it.
- Never ask a stack question of a repo that has code.
- Never suggest what is already installed.
- Never suggest from a search result that failed the source bar.
- Never write to `CONTEXT.md`, to `CLAUDE.md`, or to any file in the repo. This skill only
  reads and prints.
