# evals

Twelve cases. Run them before you push a change to a skill. Two are manual, see below.

## Which runner

**`claude plugin eval` is gated.** It exits 1 with `plugin eval is currently in
early access` before running anything, and there is no documented way to ask for
access — the command is absent from the [plugins
reference](https://code.claude.com/docs/en/plugins-reference) entirely. If you
have it, use it: it also scores the `llm` graders and runs a no-plugin baseline
arm.

```bash
claude plugin eval . --scaffold --allow-tools Bash Write Edit
```

`--scaffold` is required: every case builds its own throwaway project first,
and scaffold scripts do not run unless you ask for them. `--allow-tools` is
required because the cases need to write files and run commands. Both are
deliberate — the runner will not do either on your behalf.

**Otherwise use `run.py`**, which drives the same `case.yaml` files through
`claude -p --output-format stream-json` and scores everything that needs no
judge:

```bash
python3 evals/run.py                          # every case
python3 evals/run.py --case sizing-* --runs 1
python3 evals/run.py --dry-run                # parse and print, run nothing
```

It scores **52 of the 63 graders** — every `regex`, `tool_used`, `tool_order`
and `file_exists`. The eleven `llm` graders come back `skip`, stay out of the
denominator, and are counted in the summary. **A skip is never a pass**, the
same way `NOT RUN` is never `none`.

**A session that never started is an error, not a score.** `claude -p` with no login
answers "Not logged in" as a one-turn success at cost 0. Scored, that read as the plugin
failing 2/8. `run.py` now raises with the fix instead. Note the trap: a session inside the
desktop app does **not** pass its login to a child `claude -p`. Run the evals from a
terminal where `claude auth status` says `loggedIn: true`.

`evals/test-run.py` is its contract test — parser and graders, no model, no
cost. It is in `CLAUDE.md`'s `## Checks` block. `run.py` itself is not, because
it spends money.

### One thing `run.py` decides, that you should know about

**A rendered `SKILL.md` is not part of the trace.** The `Skill` tool returns the
whole skill body as a tool result, and `skills/flow/SKILL.md` contains its own
worked examples — `Quick — single-file copy change.` at line 569 and `Deep — new
subsystem, touches auth (danger list).` at 573. Count those as trace and three
weight-3 graders stop measuring anything:

| Grader | What it would do |
|---|---|
| `sizing-quick` / `announces-quick` | pass on any run that merely loaded `flow` |
| `sizing-quick` / `not-sized-heavier` | fail on every run, forever |
| `danger-list` / `never-quick` | fail on every run, forever |

So the result of a `Skill` call is dropped and everything else is kept. A skill's
body is input to the model, not evidence of what it did.

The limit, said out loud: a plain `Read` of a `SKILL.md` would land in the trace
and could fool a sizing grader the same way. Nothing in these cases does that —
the scaffolds build a throwaway project that does not contain the plugin — but do
not write a case that greps the plugin source and then judges a size with a bare
`regex`/`trace` grader.

## What each case is for

| Case | Cost | What breaks if it fails |
|---|---|---|
| `sizing-quick` | low | A typo fix drags the human through questions |
| `sizing-standard` | low | Borderline work gets sized by coin flip, so Quick skips the questions |
| `sizing-deep` | low | A new subsystem gets built with no plan and no questions |
| `danger-list` | low | Secrets work slips through at Quick with nobody told |
| `auto-trigger` | low | Work never reaches `flow` at all, so nothing ever ships |
| `setup-writes-checks` | medium | Every downstream check runs a command nobody verified |
| `full-loop` | high | The skills stop handing off to each other |
| `deep-coordinator` | high | A Deep job builds every chain in one session again and outgrows its window, or the chains never merge back and the PR is missing a chain's work |
| `plans-on-tracker` | high, **manual** | A project that keeps plans on GitHub gets a file instead, or a plan nobody can close |
| `backlog-parks-extras` | low | A three-feature prompt ships as one PR or drops two features on the floor |
| `worktree-guard` | medium | A second session cuts its branch in the shared checkout and moves the folder out from under a session already working in it |
| `ship-tends-conflict` | high, **manual** | A conflicting pull request gets merged, or `ship` goes back to stopping on a conflict and making the human type `tend` themselves |

`plans-on-tracker` is **manual**. It needs a real GitHub repo with issues on and
a logged-in `gh`, which no scaffold can fake. `run.py` leaves it out unless you
name it: set `DEVFLOW_EVAL_REPO=owner/name` to a throwaway repo you own, then
`python3 evals/run.py --case plans-on-tracker`. Close any `devflow:plan` issue left open
by an earlier run first, or the new run resumes it instead of planning. Its second half, the resume after
a `/clear`, has no grader at all, because it needs a second session. Do that
part by hand and read the size line.

`ship-tends-conflict` is **manual** for a narrower reason, and the difference is
worth keeping straight: `plans-on-tracker` needs a real tracker, this one needs
a real **merge base**. `mergeable: CONFLICTING` is the forge's verdict on a
branch and a default branch that have both moved, so it cannot be written into a
fixture — a bare repo answers nothing and `ship` stops at step 1. Same setup:
`DEVFLOW_EVAL_REPO=owner/name`, then
`python3 evals/run.py --case ship-tends-conflict`. The scaffold opens a pull
request on that repo and lands a conflicting commit underneath it, so point it
at a repo you do not mind being written to; it closes and deletes its own
branch from the previous run before starting.

**It merges, and that is the point rather than a side effect.** Most of what it
measures lives on the *return* path from `tend` — re-read all four conditions,
tend once and never twice — so a case
budgeted to stop at the handoff would grade one rule and claim several. Letting the
loop finish is what reaches them, and a finished loop on a conflict-only pull
request ends in a merge, because that is what `ship` is for. The first draft
asserted `gh pr merge` was never called at all, which scored the single fully
correct run as the worst possible result; the grader is now an *order* —
`tend` before any merge — which is the thing that actually matters.

One rule it does **not** measure, stated plainly rather than implied: *never read
`UNKNOWN` as a yes*. `UNKNOWN` is what the forge answers for a few seconds after
a push, and no scaffold can make it appear on demand — the fixture has to wait
for a settled `CONFLICTING` or the run would open by measuring the
wait-and-re-read path instead of the handoff. The `llm` grader judges it if the
trace happens to show it, which it may well do after `tend` pushes. That is
opportunistic coverage, not measurement.

The first four are the classifier, which is the part of `flow` most likely to
drift and the only part with correction data behind it
(`~/.claude/devflow/overrides.md`). They cut themselves off after a handful of
turns — the size announcement is all they measure, and letting the work run
would multiply the cost for no extra signal.

`sizing-standard` is the odd one out and worth understanding before you trust a
green run from it. The other three use requests nobody would argue about, which
is what makes them stable — and blind to the middle. This one deliberately uses
a borderline request, the same prompt `full-loop` builds, because that is where
the classifier actually slips: over six observed runs of that prompt, five came
out Standard and one came out Quick. **A ~1-in-6 flip will show green on three
runs most of the time.** Treat a single clean pass here as weak evidence, and
if you are changing the size table, run this case with `--runs 10`.

It also carries the only grader that checks *when* the size was announced.
`flow` promises the size line before any other output, and every `announces-*`
regex in this directory would pass on a transcript where it arrived three turns
late — one real run opened with "I'll size this first. Let me look at the CLI
code." A `contains` pattern cannot see position, so that one is an `llm` grader.

`auto-trigger` is the only case that does not type the slash command, and it
exists because every other case does. Explicit invocation cannot tell you
whether `flow` would have fired on its own — and in real use it did not. A
request to add a favicon ran to completion, about a hundred tool calls without
a single Skill call among them, and stopped at "Ready to commit if you'd like"
with the work uncommitted on the default branch. The human had to ask for the
PR, which was then made by hand and merged, which `submit` forbids.

`flow`'s instruction to call `submit` was never wrong. It never loaded. Every
other case in this directory starts one step after the step that broke, which
is why five green runs said nothing about it.

**It is still red, and it is the only one.** First measured run, 20 Aug 2026,
the first time any of these cases could be executed at all:

```
auto-trigger   FAIL  0/5 weighted
  FAIL reaches-flow-unprompted   w=3  0 call(s), wanted at least 1
  FAIL announces-a-size          w=2  not found in the trace
```

Six of seven cases — seven was the count that day; there are eleven now — pass every grader `run.py` scores. This one fails both of
its, on a plain-English request — *"the README description for this CLI is too
dry, reword it to something friendlier"* — which is exactly the shape the case
was written for. Nothing here has regressed; this is the original bug, still
unfixed, now with a number against it.

**Do not treat this as a flaky case to be re-run.** It is the most consequential
gap in the plugin: if `flow` does not fire, nothing downstream of it runs, and
every other green case in this directory is measuring a loop that was never
entered. The README's web section already concedes half of this — that you have
to start it yourself there. What this case says is that the same is true
locally, for a request that never mentions code.

`full-loop` is the expensive one and earns it. All three bugs found in the
first real end-to-end run lived in the **seams** between skills, not inside
any one of them:

- `flow` never reached `submit`
- `submit` could not tell what the default branch was, so it committed to it
- the bash hook rewrote `npm test` into something no permission rule could
  match, so `build` silently ran a different command instead

None of those are visible from a single skill. Only running the loop finds
them, which is why one case pays for the whole suite.

## Running less

```bash
claude plugin eval . --scaffold --allow-tools Bash Write Edit --tag sizing
claude plugin eval . --scaffold --allow-tools Bash Write Edit --case 'sizing-*'
claude plugin eval . --scaffold --allow-tools Bash Write Edit --runs 1
```

The classifier tags are the cheap everyday loop. Run everything before a
release.

## Reading a failure

Every case carries an `expected_outcome` in plain English. Read that first,
then the grader that failed — the grader names the promise it was checking,
not just the pattern it did not find.

`--runs 3` is the default and it is not padding. Watching the same request
three times produced two different but equally valid implementations, so a
single green run proves less than it looks. A case that passes twice and fails
once is a real finding about the skill, not noise to re-roll.

## Ablation

Pointing the runner at a path (`.`) runs one arm. Pointing it at the installed
plugin adds a no-plugin baseline and reports the delta:

```bash
claude plugin eval devflow@eddiechok-devflow --scaffold --allow-tools Bash Write Edit
```

Worth it for the sizing cases, where the question "does the plugin change
anything?" has a real answer. Not worth it for `full-loop` — without the
plugin there is no `flow` to call, so the baseline arm measures nothing.

## Adding a case

Add one when something breaks in real use, not when it sounds good. The same
rule the plugin applies to itself. A case that has never corresponded to a
real failure is a bill you pay on every run forever.

Copy the nearest existing directory. Prefer `regex`, `tool_used`,
`tool_order` and `file_exists` graders over `llm` ones — they cost nothing,
they never drift, and most promises in these skills are mechanical enough to
check that way. Reach for an `llm` grader only when the promise genuinely is
about judgement, as with test-first ordering.

One trap worth knowing: **`tool_used` counts attempts, not successes.** A
command that was refused still counts as used. `full-loop` was written with a
`tool_used` grader meant to catch the hook blocking `npm test`, and it passed
on a transcript where every `npm test` was denied. When what you care about is
that a command *ran*, assert on something only a real run produces — output it
prints, a file it writes — rather than on the call being made.

A second trap, from the same case: **do not assert on output only a hook
produces, unless the hook is certain to fire.** `full-loop` used to look for
`exit=\d`, printed by bash-guard's wrapper, as proof the wrapper had run. But
the wrapper only fires on a *bare* check command, and Claude reliably writes
`npm test 2>&1 | tail -25` first — which trips `ALREADY_SHAPED` and makes the
hook stand down, exactly as designed. Across 15 runs not one check command was
bare, so the grader failed every time while the hook was in perfect health. It
was measuring Claude's phrasing habits.

The lesson generalises: a hook's own contract belongs in a direct test of the
hook, not in an eval transcript. `hooks/test-bash-guard.py` checks all of it —
including the `allow` that regression was about — deterministically, in under a
second, for no tokens. Reach for an eval grader only for what needs a real run.

A third trap, from `deep-coordinator`: **a subagent's tool calls are in the
parent's trace too.** Its "the session never calls `build` itself" grader
failed the first paid run on the two builders' own calls to `build`, which were
the correct behaviour. When a `tool_used` grader means the session and not its
agents, set `session_only: true`; the default counts both, so no older case
changed.

A fourth, from `worktree-guard`: **`max_turns` is a grader you did not write.**
That case scored 1 of 3 on its first paid run, and the failing grader was the
last step in the sequence. It read as the skill being unreliable, and a cause
was proposed for it. It was the budget: `max_turns: 10`, against a step whose
final `checkout -b` lands anywhere from tool call #8 to #13 — so the runs that
passed under it were the ones that happened to get there early. Raised to 20,
the same skill scored 3 of 3. Nothing in the report says "ran out of turns" — a truncated run
and a run that chose not to act look identical in the output, and the graders
that already passed keep passing, so the failure looks specific rather than
positional.

Two habits come out of it. **Budget from the trace, not from taste**: run the
case once with `--keep-temp`, find the last call a grader depends on, and leave
real room above it. And **suspect the budget first when the graders that fail
are the late ones** — a case where the early graders pass and the last one does
not is the shape truncation makes.

The wider rule: this repo's reviewer flagged the budget on this very case and
`hardcase` argued it away, on reasoning that was sound and wrong. Neither agent
could run the thing. When a review and a measurement disagree, the measurement
is the one that has met the model.

Check a new grader both ways before trusting it. Point it at a transcript
where the skill did the right thing **and** one where it did not; a grader
that cannot fail is worse than no grader, because it reads as coverage.
