---
name: plan
description: "Use for Deep work - a new feature, a new subsystem, a change across many files, or anything you cannot yet name the files for. Writes the plan down as reviewable pieces with chain letters, or revises one already written, then runs one builder agent per chain until the branch carries every piece. Called by flow after its rounds of questions on Deep work, and after flow's own step 0b on a resume. Also safe to start by hand as /devflow:plan, which does flow's step 0b check itself, then writes or revises the plan and stops - flow builds it from there."
argument-hint: "[request: the words the human typed] [answers: the agreed rounds of questions] [resume: <#n or .devflow/plans/path>, if flow already found a match] [new-work, if flow decided a fresh branch]"
allowed-tools: Bash(git status:*), Bash(git branch:*), Bash(git checkout -b:*), Bash(git worktree:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(git merge-base:*), Bash(git merge:*), Bash(git tag:*), Bash(git log:*)
---

# plan

Write it down, revise it, resume it, and run one builder per chain. Report back to
whatever called this skill.

Why these rules are what they are: [docs/plan.md](../../docs/plan.md). Read it only if a
rule looks wrong.

## What you are given

`flow` calls this skill for Deep work: on new work, after its rounds of questions, with
the request and the agreed answers; on a resume, after its own step 0b already found the
match, with which plan it is. Either way `flow` calls `submit` itself once this skill
reports back — this skill never calls `submit`.

**Started by hand — `/devflow:plan`** — nothing has checked for a match yet, so this skill
runs that check itself first, the same lookup `flow`'s own
[step 0b](../flow/SKILL.md#step-0b--is-this-plan-already-running) uses: a file under
`.devflow/plans/`, and, when `## Plans` says `github`, an open `devflow:plan` issue whose
subject matches. A match means revise; no match means write a new one. See "Started by
hand" below for what happens once it is written.

## Research first

On a **new** plan, before the pieces are written, answer what is still open: start one
`devflow:researcher` per open question, **at most 3**, and often just 1. An open question
is something the pieces will depend on that the request, the agreed answers and the repo
do not already settle — what the repo has now, how others solve it, what an API really
does.

**Zero is a real answer.** When those already answer everything, start none, print
`– **research** no open question`, and the plan has no `## Findings`.

**On a `github` tracker, match an open plan issue first**, with the lookup "Write the
plan" uses. A match is a resume, and research run before it is paid for and thrown away.

**A resume skips research** — the plan already holds its findings. **A revise runs it
only when the revise brings a new open question**, and adds lines to `## Findings`
without rewriting one.

What comes back goes into the plan as `## Findings`, one line each, every line naming its
source. Read [references/research.md](references/research.md) before starting one: how to
pick the questions, what each agent is given, what to do where agents are not permitted,
and the output lines.

## Write the plan

Split the work into pieces. Each piece must be:

- **One reviewable change.** Size it by what makes a sensible diff, not by what fits in memory.
- **Marked as depending on another piece, or not.**
- **Given a chain letter**, which is what decides whether it runs beside another piece or after it.

Before the plan is shown, check coverage the other way too: **every part of the request
maps to a piece, and a part with no piece gets one.** A plan that builds less than what was
asked is as wrong as one that builds the wrong thing.

"Independent" is stricter than "different files". Two pieces are only independent if
**neither depends on a design decision the other makes**. Two unrelated endpoints,
independent. One defines a type the other consumes, **not** independent — both will finish,
both will pass their own tests, and it will break when they are joined.

Write it where the project keeps plans. Look for a `## Plans` block in `CLAUDE.md`:

```markdown
## Plans
- Tracker: github
```

**No block, or `local`, means a file**: `.devflow/plans/<short-name>.md`.

**`github` means an issue.** First list the open ones — the same `gh api` call the "What
you are given" match check above uses, or [flow's curl fallback](../flow/references/curl-fallback.md)
with no `gh` — and if one already matches this work, **that is the plan**: a session was
cleared after planning and before the first commit, which the match check above would not
otherwise catch mid-run. Resume it, and do not open a second. Otherwise open one with the
label `devflow:plan`, the plan name as the title, and the plan below as the body:

Write the body to a fresh file outside the repo — never a fixed path, which another
session or another user can reach first:

```
mktemp "${TMPDIR:-/tmp}/devflow-plan.XXXXXX"
```

The path it prints is `<body file>` below. Remove it after.

```
gh api repos/{owner}/{repo}/issues -f title="<what this is>" -F body=@<body file> -f 'labels[]=devflow:plan' --jq .number
```

**Never under `.devflow/plans/`** — on a `github` project that file is what the issue replaces, and a
file left there makes the next match check find two plans for one job.

Then print one line, exactly once, so the number is in the transcript:

```
✓ **plan** #45
```

**If that fails, write the file and say so in one line.** With no `gh` installed, "that" is
the curl fallback, so try it before the file. No auth, a refusal from the proxy, a failed
`curl` — none of those is a reason to stop. A plan in a file is a plan: `✗ **plan** github
asked for; wrote .devflow/plans/<name>.md — gh said <the error>`, naming `curl` in place of
`gh` when that is what failed.

Either way the plan has this shape:

```markdown
# <what this is>

Issue: #123 (if there is one)
Branch: <type>/<short-name> (written once the branch is cut)

## Assumptions
- Took the recommendation on X because no answer was given

## Findings
- The settings API reads every flag in one place — src/api/settings.ts:42

## Pieces
1. [independent: no] chain: A — Add the storage column and migration
   Verify: pnpm test src/db
   Done when: the column exists and the migration runs clean on an empty db
2. [independent: no] chain: A — Read it in the settings API
   Verify: pnpm test src/api/settings
   Done when: GET /settings returns the stored value
3. [independent: yes] chain: B — Rate-limit the public search endpoint
   Verify: pnpm test src/api/search
   Done when: a sixth request inside a minute comes back 429
4. [independent: no] chain: final — List both routes in the API index
   Verify: pnpm test src/api
   Done when: GET /api lists settings and search
```

**Every piece carries a `Done when:` line.** `Verify:` is the command that goes green;
`Done when:` is the observable state that means the piece is finished and the next one
may start. One line, stated as something you can check, not as intent.

**Every piece also carries a `chain:` letter**, and the letters are the plan's real
structure: one builder takes one chain, and the chains run at the same time, in separate
worktrees, on separate branches that get merged back. Four rules decide the letters:

- **A chain is pieces that depend on each other, built in order.** An independent piece is
  a chain of one. Number the pieces as a single list, and within a chain write them in the
  order they must be built — a builder works down its own letter, top to bottom, and never
  touches another's.
- **At most 4 pieces in a chain.** A chain is one builder's whole session, and a fifth
  piece is a window it cannot finish in. Split the work into more chains, or move the tail
  into one that runs after.
- **Two chains never edit the same file.** Not rarely — never. Chains are branches, and
  two branches editing one file is the merge conflict this skill stops the job on. Two
  pieces that want the same file belong in one chain.
- **A piece that must touch a shared file is `chain: final`.** That chain runs alone, after
  every other chain has merged, so it sees all of their work. It is where the index, the
  router, the docs page or the changelog entry goes — the file every chain would otherwise
  have written into at once.

**`build` commits each piece as it goes green**, which is what makes a long plan
survivable: you may `/clear` between pieces and pick up from the plan plus
`git log <default branch ref>..HEAD`. The plan says what the pieces are; the log says which
of them exist.

The plan itself is still not a progress tracker — nothing writes back to it, file or issue,
except the `Branch:` line written once the branch is cut and the `## Changes` line a revise
appends. It is the spec `review`'s second axis reads.

## Revise the plan

A revise touches only pieces with no commit in the log yet — check `git log <default
branch ref>..HEAD --oneline` against each piece's subject first. **A change to a piece
already built is not a revise of that piece; it is a new piece**, appended after it, in the
same chain if it depends on the built one or a fresh chain if it does not. Never edit a
built piece's own lines — the commit is the record of what actually shipped, and rewriting
the plan under it would make the two disagree silently.

Every revise appends one line under `## Changes` in the plan, file or issue, so `review`'s
spec axis can see the plan changed and why:

```markdown
## Changes
- 2026-09-28: split piece 3 into 3 and 3b, so a chain never exceeds 4 pieces — why: the
  request grew a filter the endpoint alone could not carry
```

Date, what changed, why — one line per revise, appended, never rewritten. Create the
`## Changes` section if this is the first revise.

## Resume it

Read the plan, then read what exists — three things, not one: `git log <default branch
ref>..HEAD --oneline`, `git branch --list`, `git worktree list`. The plan says what the
pieces are, the log says which are built, and the branches and worktrees say which chains
were started. **Announce where you are picking up** —
`Deep — resuming email-alerts, chain A merged, chain B started` — then go straight to "Run
one builder per chain" with the chains that are not done, skipping the questions: they
were settled when the plan was written and it holds their answers.

The mechanics of telling a started chain from a finished one, a whole chain from a stopped
one, and a dirty tree from a clean resume are worked examples, not summarised here — read
[references/resume.md](references/resume.md) before resuming anything.

## Show the pieces, and wait

**On a new plan from `flow`, stop once before the first builder.** Show the pieces:

```
→ **pieces** 3 in 2 chains — A and B at once
1 A — Add the storage column and migration
2 A — Read it in the settings API
3 B — Rate-limit the public search endpoint
```

Then ask one popup: go, or change something. No popup tool: `Reply "go" to start the
builders, or say what to change.` A change is a revise, and the pieces show again. A resume
does not stop here: its pieces were approved when it was written.

## Run one builder per chain

**This session coordinates. It does not build.** So each chain goes to a fresh
`devflow:builder` agent, which works in its own git worktree on its own branch, and what
comes back here is a `branch:` line and five lines per piece, not a build.

**The chains run at the same time.** That is the whole point of the letters: the pieces
inside a chain depend on each other, and the chains do not, so building chain B after
chain A buys nothing but wall-clock time.

**Before the first chain spawns, point the worktrees at this branch.** A subagent's
worktree is cut from the repository's **default branch**, not from where this session is
standing, unless `worktree.baseRef` says `"head"` — Anthropic's worktrees documentation is
explicit about it. On a branch stacked on another PR, or on any chain after the first merge,
a worktree cut from the default branch is missing the base it was supposed to build on, and
nothing says so: the chain builds, its tests pass, and the diff is inexplicable at the merge.

Read `worktree.baseRef` from `.claude/settings.local.json`, `.claude/settings.json` and
`~/.claude/settings.json`. **If any of them already says `"head"`, print nothing** and carry
on. Otherwise merge `{"worktree": {"baseRef": "head"}}` into `.claude/settings.local.json`
— create the file if it is missing, and keep every key already in it — then print exactly
one line:

```
✓ **settings** wrote worktree.baseRef = head to .claude/settings.local.json
chain worktrees branch from here, and so will your own --worktree sessions
```

**Never write `.claude/settings.json`.** That one is committed, and this is a preference
about this machine, not a change to the project. If the write fails — no permission, a file
that is not valid JSON — print `✗ **settings** <why> — building the chains one at a time`
and take the sequential path below. Spawning
chains from the wrong base is the failure this whole step exists to avoid, so falling back
is the safe answer, not a lesser one.

**A setting written in this run is not in force in this run.** Settings are read when a
session starts, and this session started before you wrote the file. So the run that writes
it is the one run that cannot use it: every worktree it cut would come off the default
branch anyway, and the check below would catch that only after four builders had finished.
**Do not spawn chains on the run that wrote the setting.** Print exactly one line:

```
– **chains** worktree.baseRef was just written — this run does not spawn chains
```

Then build this job on the sequential path — the one under "Where the harness cannot give
a builder its own worktree" below: one builder per **chain**, in plan order, one at a time,
spawned **without** `isolation` on the Agent call, so it commits on this branch and there
is no merge step. The run that finds the setting already there is the run that spawns
chains.

**The check below still runs on the runs that do spawn.** A settings file that says
`"head"` is not proof the value reached this session either — one edited by hand a minute
ago reads exactly like one loaded at start-up. So finding it does not excuse trusting it.

**Stand on the feature branch first**, on every path, the sequential one included. No
`build` runs in this session, so nothing else cuts it. **Read the plan's `Branch:` line
before anything moves.** If it names a branch other than the one you stand on, and
`git rev-parse --verify --quiet refs/heads/<branch>` still finds it, stop:
`✗ **plan** <plan> is on <branch>, not here` — the built pieces live there. Otherwise, on
the default branch, or when `flow` passed `new-work`, cut it from the default branch ref,
the same rule `build` follows; on any other branch, keep it:

```
git checkout -b <type>/<short-name> <default branch ref>
```

**Then write `Branch: <name>` into the plan**, under its `Issue:` line, naming the branch
you now stand on, cut or kept. If it already names this branch, write nothing. Only a line
whose branch is gone is replaced. The line is how `flow`'s step 0b tells this plan's resume from
new work — a base tag comes only with chains, and a commit only with a finished piece. A
file gets it by edit. An issue gets it by reading the body, adding the line, writing it to
a fresh `mktemp` file, and:

```
gh api -X PATCH repos/{owner}/{repo}/issues/<n> -F body=@<body file>
```

With no `gh`, the curl fallback sends the same PATCH as JSON `{"body": ...}`. If both fail,
print `✗ **plan** could not write Branch: to #<n> — <the error>` and carry on.

**Then tag this branch's tip**, before the first spawn, so the base survives a `/clear`:

```
git tag devflow/<plan short-name>/base HEAD
```

A local tag, never pushed; step 6 deletes it. If the tag already exists, this is a resume:
leave it, it is the base the started chains were cut from.

The loop, from the plan's chains — right after the plan is written, or wherever "Resume it"
said you are picking up:

1. **Spawn one `devflow:builder` per chain, up to four at once, with `isolation:
   "worktree"` on the Agent call.** The worktree is asked for here, per spawn, and not
   pinned in the builder's frontmatter, so the sequential path below can spawn the same
   builder without one. Give each exactly three
   things: the plan body **pasted in full**, never a path — the plan file is untracked in
   the tree you are standing in, so a worktree cannot resolve one — the chain letter, and
   `clean` or `dirty`. Nothing else: not this session's reasoning,
   not what another builder said, not a hint about the seam. **Four is the cap**; a fifth
   chain waits and starts when a slot frees. Do not spawn `chain: final` here — it runs
   alone, at step 7.
2. **Wait for every report and read all of it.** One `branch:` line, then `piece`, `test`,
   `commit`, `seam` and `stuck` for each piece that chain built — sixteen lines for a
   chain of three. A report with fewer lines than its chain's pieces need, one that came
   back as prose, one with no `branch:` line, or one saying `commit: none` beside
   `stuck: no`, did not finish: treat it as `stuck: yes` with that chain's tree dirty.
   A piece is only done when its commit is in.

   **Then check the branch it reported was cut from here**, once per chain, before it
   counts as done:

   ```
   git merge-base --is-ancestor devflow/<plan short-name>/base <that chain branch>
   ```

   A non-zero exit means the worktree was cut from the default branch after all: the
   setting did not take in this session, and everything that chain committed is built on
   the wrong base. **Do not merge it.** Stop the loop and print:

   ```
   ✗ **chains** chain <letter> branched from the default branch
   the setting did not take; restart the session and run flow again to resume
   ```

   Leave that chain's worktree and its branch on disk — its commits are the work, and a
   restarted session reads exactly that state at "Resume it". A merge here would bury a
   wrong base under a merge commit, which is the one outcome nobody can unpick later.
3. **Print what came back**, one shaped line per branch and one per piece — never as
   prose:

   ```
   ✓ **branch** devflow/chain-b

   ✓ **piece** 2 — Read it in the settings API
   tested at: GET /settings, commit a1b2c3d

   ✓ **piece** 3 — Show it on the settings page
   tested at: the rendered page, commit e4f5a6b
   ```

   **Print the seam under the label `tested at:`**, never as `seam:` — that is this
   plugin's word for it, and the person reading the report has not read this skill. A
   piece whose builder reported a concern still prints `✓` — the commit and the tests are
   in — with the concern appended: `... commit e4f5a6b — concern: <text>`. Do not verify
   the work yourself — the commits and the test lines are the evidence, and rebuilding it
   here is what fills the window this loop exists to protect.
4. **On any `stuck: yes`** → stop spawning new chains, and let the ones already running
   finish and report — killing them throws away pieces they have already committed. Then
   stop the job and print, in the builder's words:

   ```
   ✗ **chains** chain <letter> stuck at piece <n>
   <what the builder ruled out>; next: <what it would look at next>
   ```

   If its line says `tree dirty`, say that too, in the same line, so a
   resume hands the next builder the right flag. **Do not merge anything**,
   and leave the finished chains on their branches: this skill's own resume reads exactly
   that state and picks the job up before step 5. Do not spawn another builder at the same
   chain, and do not finish the piece in-session — the human decides.
5. **Merge each chain branch into this branch**, in plan order, once every chain has
   reported. The branch name is the one that chain reported on its `branch:` line; you did
   not choose it and you do not guess it. Check before you merge:

   ```
   git merge-tree --write-tree <this branch> <chain branch>
   ```

   **A non-zero exit is a conflict, and it stops the job.** Name the two chains and the
   files, and hand it to the human. Never resolve it yourself: the plan says two chains
   never edit the same file, so a conflict means the plan was wrong, and a wrong plan is
   fixed in the plan, not patched over in a merge. A zero exit means merge it:

   ```
   git merge --no-ff <chain branch>
   ```

   `--no-ff` always, so every chain leaves one merge commit naming it and the builders'
   own SHAs stay exactly as they reported them. **This merge is local**, into the feature
   branch, on this machine. It is not a pull request merge and it never touches the
   default branch, so what `submit` and `ship` promise is unchanged.
6. **Remove each merged chain's worktree and branch.** `git worktree list` says where they
   are:

   ```
   git worktree remove <path>
   git branch -d <chain branch>
   ```

   A worktree the harness already removed is not an error — say nothing and carry on.
   `-d`, never `-D`: a branch git refuses to delete is a branch whose work is not in, and
   that is worth stopping for rather than forcing past. Once the last chain is merged,
   delete the base tag too: `git tag -d devflow/<plan short-name>/base`.
7. **Then `chain: final`, if the plan has one** — one builder, alone, after every other
   chain has merged, so it sees all of their work on this branch. That is why it exists:
   its pieces touch the files every other chain would otherwise have written into at once.
   Same loop, steps 1 to 6, for that one chain, with its own tag —
   `devflow/<plan short-name>/final-base` — cut after the merges, because the base moved.
8. **When the last chain is merged** → report back to whatever called this skill. `flow`
   calls `submit` from there, as for every size.

**Where the harness cannot give a builder its own worktree** — no `isolation` option on
the agent tool, or the first spawn using it fails — say so once:

```
– **chains** no worktree isolation — one builder at a time on this branch
```

Then run the sequential path: one builder per **chain**, in plan order, one at a time,
spawned **without** `isolation` on the Agent call, so it works on this branch and commits
here. Same three inputs, same report — its `branch:` line names this branch. No merge
step, no cleanup and no tag, because there are no chain branches — and **no base check at
step 2 either**: there is no tag to check against, and `git merge-base` against a missing
tag exits non-zero for that reason alone, which would stop a healthy job with a false
message. The `branch:` line naming this branch is the whole check on this path.
`chain: final` is just the last chain. Nothing is lost but the wall-clock time. Say it
once for the whole job, not once per chain.

**Where the harness only starts agents when asked** — the same restriction `review` names,
a plan one, not a web one, and you tell by looking at your own instructions — ask once,
before the first chain:

```
This harness only starts agents when you ask. Say "build the chains" and one builder runs per chain.
```

If that answer does not come, build every piece in this session through `devflow:build`,
one at a time, in plan order, exactly as before this section existed. Print one line —
`– **chains** agents not permitted — building in-session` — and carry on. Nothing is lost
but the window. Ask once for the whole job, not once per chain.

## Started by hand

`/devflow:plan` run directly — not called by `flow` — still needs rounds of questions
before it writes a new plan, or before it revises one whose open question the plan
cannot be written without. Ask them by the rules in flow's
["Asking questions" section](../flow/SKILL.md#asking-questions--rounds-until-no-answer-would-change-the-build),
not copied here.

Then write the plan, or revise it, and **stop.** Do not run "Run one builder per chain" —
that only ever runs from `flow`, which sizes the work, cuts the branch and calls `submit`
when the chains are done. Print the plan's number or path, then the next step:

```
✓ **plan** #45
→ **next** /devflow:flow #45 builds it
```

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **plan** #45`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never build more than one chain's pieces yourself. Each chain is a fresh
  `devflow:builder` agent, spawned per the loop above.
- Never spawn more than 4 chains at once, never let two builders share a branch, and never
  resolve a chain merge conflict yourself — a conflict means the plan was wrong.
- Never skip a builder's report. A `branch:` line and five lines per piece, read in full
  before that chain counts as done; fewer is `stuck`.
- Never build a Deep piece in-session while agents are available. Only when the harness
  refused, and say so.
- Never start a builder on a new plan before the human says go to its pieces.
- Never rewrite a piece already built. A change to it is a new piece, not an edit.
- Never revise without appending a `## Changes` line — date, what changed, why.
- Never call `devflow:submit`, `devflow:review` or `devflow:ship` from the by-hand path.
  Only `flow` calls `submit`, and only a human starts `ship`.
- Never ask a question `flow`'s rounds already settled. A resume skips the questions.
