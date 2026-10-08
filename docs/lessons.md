# Capturing lessons

Built now, from [#57](https://github.com/eddiechok/agent-devflow/issues/57). Two skills carry it: `lesson` collects, `lesson-review` reads and proposes. The short version is in the [README](../README.md#the-skills).

Until about 2026-10-08, use devflow on the Mac. Use a web session only when you are away from the Mac, and start it with "use the devflow flow skill" ([docs/web.md](web.md) says why) — waste counting cannot see a web session at all, below.

## The goal

Improve all of devflow from real runs, not only `flow`'s sizing. Before this, the only piece was `~/.claude/devflow/overrides.md`, and it only collected ([docs/flow.md](flow.md)). `flow` now records overrides through `devflow:lesson` instead, so everything collects in one place.

Collecting is the first step of a loop:

1. **Collect.** Log each mistake when it happens.
2. **Review.** Read the lessons together. Find the patterns.
3. **Fix.** Change the skill text. Patch what is there before adding anything new.
4. **Check.** Turn the lesson into an eval case under `evals/`. Run every eval on the old skill and on the new one. The new case passes, and nothing else gets worse.

Step 4 makes each lesson a test that stays. The same mistake cannot come back without an eval failing.

**A human approves every skill change.** devflow never edits its own skills without one. One bad lesson, applied without a human, could quietly make every skill worse.

## Two kinds of lesson

| Kind | Example | Goes to | When |
|---|---|---|---|
| devflow | "`flow` sized a checkout change Quick. It was Deep." | the lessons repo | when it happens |
| project | "the tests need the sandbox key" | that repo's `CLAUDE.md`, or a `.claude/rules/` file for one package | at the end of `submit`, in the same PR |

The session that did the run sorts each lesson. It knows what went wrong. A fresh agent does not, so no subagent does this.

A project lesson goes in the PR, so the human sees it and approves it with the work.

## Where project lessons go

The root `CLAUDE.md` loads into every session. Claude Code's docs say to keep each `CLAUDE.md` under 200 lines, because a longer one costs context and is followed less well. They name path-scoped rules as the place for instructions that matter for only part of the codebase ([memory docs](https://code.claude.com/docs/en/memory)). A `.claude/rules/*.md` file with a `paths:` glob loads only when Claude reads or edits a file it matches.

So `submit` sorts a project fact by the files it is about:

- **One package** — the nearest folder above the files with its own `package.json`, `pyproject.toml`, `go.mod` or the like, below the repo root. The fact goes to `.claude/rules/<package>.md` with `paths: <package>/**`, and `submit` makes that file the first time. A monorepo's backend facts then load only when Claude works in the backend.
- **Anything else** — a single-package repo, a fact across packages, a fact about no file. The root `CLAUDE.md`, as before.

A `.claude/rules/` the repo ignores falls back to the root, because a file nobody commits is lost with the checkout. `reviewer` reads the rule files that match a change, and `hardcase` counts them as written rules, so a fact moved into one is still checked in review.

Nested `CLAUDE.md` files also load only when needed, and were the other choice. Path-scoped rules won because the docs name them for this, and they keep the facts out of the code folders.

## Where devflow lessons go

One line per lesson, in `lessons.md`, in a **private** repo: `eddiechok/devflow-lessons`.

```
2026-10-02 | shop-repo | build | mistake | wrote the test after the code | shop-repo#12 | "test first, always"
```

Each line has seven parts: the date, the project, the skill, the kind (below), what went wrong, a link to the proof (a PR or a commit), and the human's own words when they corrected it. The proof lets the review check the lesson against what really happened. The human's words hold the fix, not only the fact that something broke.

**Not in this repo's issues.** This repo is public. A lesson from a client project can name the client, a product or a bug. A leak cannot be fully undone.

**A file, not issues.** A web session has no `gh`, but it can push a file. One file also reads top to bottom at review time.

**One file for every project.** Lessons kept per project scatter, and a pattern only shows when you read them side by side. That is why `overrides.md` was global too.

`overrides.md` moved into this file. On a hosted session `~/.claude` is lost when the session ends, and the file with it.

## Mistakes, waste and ideas

A run can be correct and still be slow, cost too much, or ask too many questions. So a devflow lesson has one of three kinds:

| Kind | Example | How it is found |
|---|---|---|
| mistake | "`flow` sized it Quick. It was Deep." | the signs below, when they happen |
| waste | "The human answered 'yes to all' 9 times in 10." | counted from saved sessions, at review time |
| idea | "The PR body could carry a screenshot." | the human, by hand, or a research pass |

## What writes a line

A good run writes nothing. Lines come from three places.

- **By hand**, for any kind: `/devflow:lesson "..."` for a mistake, `/devflow:lesson idea "..."` for an idea.
- **Automatically**, for the three clearest signs:
  - `flow`: the human used `--quick` or `--deep`. This exists today.
  - `review`: `hardcase` refutes a finding. The finding was a false alarm.
  - `ship`: Verify fails after the deploy.
- **Later**, only if the data asks for them:
  - the human stops `build`, or reverts what it wrote
  - `submit`'s checks pass, but CI fails
  - `tend` blames the wrong cause
- **Counted, for waste**, by `skills/lesson-review/count-waste.py`, not during a run. It reads
  `~/.claude/projects/*/*.jsonl` — one JSON object per line, undocumented, so it skips
  whatever line it cannot make sense of and counts the skips rather than guessing a shape —
  plus each session's subagent transcripts, saved beside it. Per devflow skill, it counts:
  - how often the human answered "yes to all", charged to whichever skill's command was open
    — a popup answer where every pick was the "(Recommended)" option counts as one too,
    so the signal survives `flow` asking in popups
  - permission prompts — but the session file only ever records a *denial*
    (`toolDenialKind`); an approved prompt leaves no trace at all, so approvals print as
    `"not recorded"` rather than a guess
  - each `flow` run's size, next to that session's whole duration and cost from its last
    `cost-state` record
  - how many `review` runs happened, and how many reported no findings — every line of
    the run's `## Worst of each` block says `none` or `skipped`

  Only devflow's own skills are counted. `/model` and other built-in commands are not skill
  runs, and another plugin's skills are left out.
  A resumed or forked session copies earlier records into a new file. Each record counts
  once, in the oldest file that holds it: the one made first, which a Mac records and
  other systems only guess at from the last change. A `review` run cut off before its
  `## Worst of each` block is finished by the file it was resumed into.

  This needs no new logging. Archived sessions count: archiving keeps the saved file, and a
  subagent's run is saved beside it. Deleted sessions do not count, and neither do web
  sessions — their saved sessions are lost when the container ends, so nothing here can see
  them at all.

## Reaching the lessons repo

Tested on 2026-09-25.

- **Mac:** the active `gh` account has write access to the repo. A push works.
- **Web:** by default a session reaches only the repo it was opened on, and it has no `gh`. A clone of a second repo fails with `could not read Username`. After the `add_repo` tool adds `eddiechok/devflow-lessons` to the session, `git push` to `main` works (probe commit `c03e36f`). `add_repo` showed the human no approval prompt.
- **Fallback:** if `add_repo` fails, the session prints the line in its reply. The human copies it.

## The review step

A skill the human starts by hand, in a new session, for example once a month. It reads `lessons.md` and proposes skill changes, each with an eval case. It uses no subagents unless the file gets big.

Four rules:

- **Only repeats.** A skill changes only when the same kind of mistake shows up at least twice. One mistake is a note, not a pattern. A line with no repeat after about 30 days leaves the review and moves to `archive.md`, so nothing is lost.
- **A size budget.** Each skill has a size it may not grow past. Every proposal states its net change in words, and a review deletes as well as adds. More text is not better: longer instructions cost more and can score worse.
- **A rule becomes a check.** When a lesson is really "never do X", it becomes a hook or a script check, like the bash guard in `hooks/`, not another sentence in a skill. A sentence can be ignored. A check cannot.
- **Old against new.** The whole eval suite runs on both versions of the skill. A change that makes any case worse does not go in, even if the new case passes.
- **Waste and ideas prove it in numbers.** A change with no mistake behind it must be faster, cheaper or need fewer prompts, with the evals unchanged. If it cannot show that, it does not go in. This is where bloat comes from otherwise.

A research pass, like the one below, is an idea source too. Run one every few months.

## What the research says

Six research agents looked at how others do this, on 2026-09-28. The star counts were checked with `gh api`.

- **The capture and approval design holds up.** Lessons from outside signals, approved by a human, work. Lessons an agent writes about itself, unchecked, can do harm: in SkillsBench, skills a model wrote for itself scored below no skills at all, and the Reflexion paper has nothing that filters out a bad reflection.
- **Human words help.** Letta (letta-ai/letta, 24.9k stars) measured a 21% gain from skills learned from runs alone, and 37% with human feedback added.
- **Lessons go stale.** GitHub Copilot Memory stores a citation with each memory and deletes one unused for 28 days. Hermes Agent (NousResearch/hermes-agent, 249k stars) marks a skill stale after 14 days unused and archives it after 30, because otherwise its library filled with narrow near-duplicates.
- **More text can be worse.** An ETH Zurich study (arXiv 2602.11988) found that `AGENTS.md`-style context files gave no gain in task success and raised cost by over 20%.
- **Prose rules get broken.** In Claude Code issue #33603, a rule marked mandatory after one failure was broken in each of the next three sessions.
- **The closest match is obra/superpowers** (292k stars). Its lessons go straight into the skill text, a human approves each change, and changes are tested with evals before they ship.
- **Capture without proof is the common gap.** Every's compound-engineering plugin (25.3k stars) captures lessons well, but nothing shows a lesson prevented the next mistake. The eval step here is the answer to that.
