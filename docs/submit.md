# submit, in detail

Why `submit`'s steps are what they are. The steps themselves are in
[the skill](../skills/submit/SKILL.md), and the short version is in the
[README](../README.md).

Most paragraphs below were moved here out of `skills/submit/SKILL.md`, word for word;
the subsections that cite a date or a pull request were written here, about a change
that landed after the move. The skill holds the steps; this holds why they are what they
are.

## Step 1 — the branch

`build` should have done this before its first edit, so normally you are already on one. This is the safety net for when `build` did not run — you were called directly, or the work arrived some other way.

Some harnesses create the branch and forbid pushing anywhere else; Claude Code on the web does both.

## Step 2 — checks that postdate the last edit

Not "they passed earlier" — earlier is before the edit that broke them.

Running the same suite twice on the same tree prints the same result and proves nothing new; it only fills the window.

### What has to reach the screen

The real output **and the exit code** both have to reach the screen: the exit
code is what proves the run happened, and an outer loop watching this session
can only see what you actually printed.

Shape the command yourself and it
steps aside by design, taking the trimming and the exit line with it.
`${PIPESTATUS[0]}` after a `;` silently printed nothing in a real run, because
the shell was not the one that syntax assumes.

### The hook's own list

A project whose `## Checks` block names
something else gets no rewrap and therefore **no `exit=N` line**, however bare
the command was. This plugin is such a project: `python3 skills/test-frontmatter.py`
matches nothing on that list.

Never write `exit=0` yourself as though the hook printed
it; a fabricated exit line is worse than none, because that line is
what an outer loop trusts.

## Step 3 — debug leftovers

Unquoted, zsh tries to expand it before grep ever runs and fails the whole command with `no matches found` — bash passes it through, so this breaks for some people and not others.

**Markdown is excluded on purpose.** A marker in a `.md` file is prose — a code sample, a note about the convention, or this plugin's own description of it. Without that exclusion the check fails forever in any repo that documents the convention, this one included, on hits that are all documentation. Markers matter in code, because code runs.

Cleaning up someone else's debugging inside your PR buries your change in noise.

## Step 4 — the live check

Tests only check what someone thought to test. A passing suite and a clean diff can both sit on top of a feature that is visibly broken: wrong label, broken layout, right data in the wrong place.

`node src/cli.js --loud` *is* the live check for a CLI; reaching for a launcher here adds nothing.

### First-hand and second-hand

If yes, it proves
nothing — it is evidence that something answered, not that the change works.

A server that boots is second-hand about a broken
page, and it is the most common way this step gets faked: the launch worked, so the
change must have.

This is the same rule `ship` step 5 applies to a deploy, and it has to stay the same rule —
a green deploy is second-hand about a live site for exactly the same reason.

### When it does not work

An honest failure is useful. A green-looking PR over a broken feature is harmful.

## Step 5 — the review

It pins the range, finds the plan or issue if there is one, and runs both axes in fresh agents, plus `security-reviewer` when the danger list names a security item.

On work with no plan and no issue, that text is the spec the second axis reads, and without it that axis does not run.

### Why `no-behaviour:` goes on its own line

`review` only recognises it at the start of a line, so glued onto the request text it is spec, not a signal.

### Why round 2 is scoped

That is a range and another agent's report, not this session's reasoning, so `review`'s rule holds. A full re-read of the branch finds the same clean files again at the same price, and the cost of a review should go where the change went.

### Why a truncated review is a finding

A truncated review prints exactly like a clean one, which is the whole reason the line is there; dropping it here is the same failure as dropping `NOT RUN`.

### Why a `Falls` still gets checked

Two agents disagreeing is not a majority vote; it is one of them having read something the other did not, and you are the one who can go and look.

### Why `/code-review` is not here

The built-in `/code-review` is a better review than this one, and it still does not belong here: it works on an **open pull request** and comments back on it, and there is no PR yet. It used to be offered to the human at step 9, where one exists — that offer is gone now, for the reason under step 9 below.

## Step 6 — the docs

This step exists because nothing before it reads the docs. `build` tests behaviour and `review` judges the code, so a diagram that stops matching the skill it draws goes stale with no red anywhere. `docs/pipeline.md` did exactly that after the builder-per-piece change, and a human found it later. One read here is cheaper than the drift.

**It prints a shaped `docs` line because for a while it printed nothing, and that turned out to be the difference between a step and a suggestion.** Every step in `submit` now leaves one shaped line on screen — `✓ **checks** ...`, `✓ **look** ...`, `✓ **pr** updated #12`, the `✓ **review** ...` summary. Step 6 was the one that had something to report and reported nothing. Step 1 used to be silent as well; that was a different case, a branch which is already correct has nothing to say, where step 6 always has either a list of files or a look that found none — but step 1 now prints its `branch` line whenever `build` has not already put one on screen this run, for the same reason: some `branch` line is always there, and a second copy of it is noise. Silence here is ambiguous in the worst way: a run where nothing was stale and a run that never looked produce identical output, in the transcript, in the commit and in the pull request. Nothing downstream can tell them apart, and neither can the session itself on a second pass.

That is how PR #31 went wrong on 22 Sep 2026. The first pass through `submit` updated `docs/flow.md`, `docs/provenance.md` and `README.md` properly. The follow-up pass changed how `flow`'s step 0c behaves, updated none of them, and nothing objected — the reasoning for a live rule survived only in a commit message, where the next person to revise that rule would never look. The human caught it.

So the line is required in both directions, and `– **docs** nothing stale` is as much of an answer as naming three files. The step it makes honest is the one most easily lost on a follow-up, precisely because the docs were already right the first time round.

### Sorting a lesson by which repo it fits

Step 6 is also where a fact this run learned about **this project** — not devflow — gets one line added to `CLAUDE.md`, in the same commit, with the fact listed in the PR body so the human approves it alongside the work rather than finding it later. A fact about devflow itself never goes there; it goes to `devflow:lesson`, and the lessons repo `docs/lessons.md` describes. Only the session that did the run can tell the two apart, which is why no subagent does this sort.

## Step 7 — the commit

A marker removed at 3, a live-check fix at 4, a review fix at 5, a doc at 6 — any of them means step 2's run no longer covers the tree you are about to commit.

The checks always postdate the last edit, and so does the look — every fix the look makes is read by a look after it. That is the whole of the rule, stated at the last place an edit can land.

`build` commits each plan piece as it lands, so the working tree can be clean by the time you reach this step — and the fixes from steps 5 and 6 may be all that is left.

### Why the look gets up to three fixes, and the last look only reports

The look exists so the last review postdates the last edit, and the first version of the
rule sent anything it found straight under **Known issues**, so the fix-then-look loop
would end. It ended, and it also found something on almost every PR — it reads the fixes
made after the review, and those are the least-read lines on the branch. Three PRs in a
row shipped with a one-line Known issue that a minute would have fixed: #23, where line 7
of this page claimed every paragraph below was moved verbatim and one subsection was
fresh prose; #25, where the untracked plan file made a file-mode resume read the tree as
dirty; and #26, where `ship` step 6 promised that step 7 names the retargeted PRs and
step 7's template did not list them. Each one became a follow-up the human had to
remember, which is worse than the minute.

So the look then got one fix, bounded twice over. **Small**, because a fix of a few lines
is one a human can read in the PR without an agent's help. **In a file already changed on
this branch**, because a file the branch did not touch is scope the request never asked
for, and widening a PR at the last step is how a change stops being reviewable. Anything
that fails either test goes under Known issues exactly as before.

That second version also said **no further look after that fix**, to keep the loop bounded:
review, round 2, look, one small fix, done. The price was one edit on the branch that no
agent had read, named under **Evidence** so the reader knew which lines to read
themselves. On PR #65 that line was a real edge case in `flow` step 0b, and the human
asked the obvious question: why does the run end on an edit nobody reviewed?

Bounded does not have to mean unread. The loop now **ends on a read**: up to three fixes,
each followed by a look at only the lines that fix changed, and **the last look only
reports** — what it finds goes under Known issues, and a leftover bug is parked. The cap
keeps the loop finite; the report-only last look keeps every line read. Three, not one,
because the findings shrink fast but not to zero — #65 went six, two, one — and a fix a
look can check is worth more than a line the human has to. Not more than three, because
a problem that survives three small fixes is a plan problem, and that is the human's.

### Why a leftover bug is parked, and nothing else is

Known issues held three kinds of line. Most were rejected findings — a reviewer was
wrong, and here is why — or test gaps: no live check, no eval case, an axis that could not
start. Both are for whoever merges, and both are done with once the PR is. The third kind
is a leftover bug, and it is not done with: #24 named a resume that reads a plan file as
dirt, #26 wrote out a one-line fix to `ship` step 7, and #33 found `ship` step 2 had no
`UNKNOWN` case. Each sat in a merged PR body that nothing reads again, and each depended
on the human to remember it. The bounded loop is right to stop fixing; it was wrong to
stop tracking.

So a leftover bug is parked exactly as `flow` step 1b parks a feature, and the Known issues
line links to it. The two notes are not: a tracker full of "the reviewer was wrong" is
noise, and noise is how a backlog stops being read. The parking happens before the commit
because a backlog file is part of the change — it ships in the same PR that found the bug.

## Step 8 — the pull request

The answer decides what this step does, and getting it wrong opens a second pull request for one change.

The first round's assumptions were true when they were taken, and the human may already have read them.

Some harnesses expect the human to press **Create PR** themselves, and a session there can read that as a rule against opening one.

The plan is finished when the work is merged, and the issue closing is what says so on the tracker.

### The `Concern:` lines

Every `Concern:` line goes under **Assumptions**, one bullet each, with the subject of the
commit it sits under — the format prints the subject before each body on purpose, because
`%B` alone gives no boundary between one body and the next subject. That is where the human decides whether the doubt was warranted; leaving it in a
commit body nobody reads is the same as never raising it.

### The preview link

If one did, put it
first — a preview is a real build with real environment variables on a clean machine, and it catches things your laptop cannot.

## Step 9 — handing off

This step used to work the danger list out from the diff a second time and offer the human `/code-review` and `/security-review` to type themselves — a manual opinion line, because the security question had nowhere automatic to run. That offer relied on `flow`'s original danger-list read surviving to here, which it did not always do: a compaction, a long Deep job, or a `submit` invoked directly all lost it, silently, and what it dropped was the only security gate in the loop.

The `security-reviewer` plan, 24 Sep 2026, retired the offer rather than patching the survival problem again. `security-reviewer` now runs inside step 5, on `reviewer`'s own read of the danger list, whenever a human would have — and unlike the offer, it cannot be forgotten, because nobody has to remember to type it. So step 9 hands off with nothing left to offer.

### The Done report

Nine steps each print one shaped line, but they print it between whatever tool output that step produced, so a finished run is a needle-in-haystack read for anyone who was not watching live. A recap fixed that by repeating those lines at the end, and one to three `done` lines above it said what changed. #95 asked for a picture instead of a list of sentences, so the end of the run is now a report in the same shape as the Plan and Pieces reports.

Its table holds the plan's own rows, each marked `✓` or `✗`, so the human reads what was promised next to what was done. The `done` lines became its "What you will see" section. The PR body's check steps and assumptions are repeated in it, so nothing needs the PR opened to be read; the live check line is not, because a passing one says nothing new and a failing one is a `✗` line already. The recap shrank to "Needs you": only the `✗` and `→` lines still open and the Known issues — the lines a human has to act on — so a clean run ends with no such section at all. A `✗` the run later fixed is left out, or a `tend` run that fixed every failure would never end clean. So is a finding the review rejected: it sits under Known issues so whoever merges can see the call, but it asks nothing of the human, and #100's own Done report showed it reading as an open problem. Quick prints a plan but never waits for go, so its rows are the plan it printed.

## Step 8 — tracker actions

A request can ask for more than code: "close #53 as not needed, update the README, close
it with a comment saying why". Before #77, `submit` handled the README and wrote
`Closes #53`. That closes the issue only when the PR merges, as completed, and with no
comment, so the session had to close it by hand.

**The action runs once the PR is open, not at merge.** Merging is often a button on
GitHub, and then `ship` never runs. And "close as not planned" is the human's decision,
already made in the request; it does not wait on the code. Doing it after the PR exists
also lets the comment link it.

**Only the lines `flow` passed.** `flow` asks the human before it keeps an action that came
from an issue body, because closing and commenting are public, and anyone who can write an
issue could otherwise make them happen. A `submit` that went looking for actions itself
would skip that question.

## Direct mode — finishing a job on main

A project that works `direct` has no pull request to open, so `submit` has two jobs less and one more. The detail is in [the direct reference](../skills/submit/references/direct.md); `SKILL.md` only points at it from steps 1, 5, 7 and 8, so a `pr` run never reads it.

**Step 1 does not refuse main.** The refusal exists so work never lands on the default branch unreviewed, and in direct that is the point. The Rules say "in pr mode" for the same reason: a rule written for one way of working, left bare, would contradict the other.

**Review follows the size, because there is no PR to stop at.** In `pr` mode review runs on every size, since a human reads the PR afterwards. In direct, nothing stands between the commit and main, so a Quick change is not reviewed: the reviewers cost more than the change is worth, and the skipped line says so out loud rather than leaving a gap. Standard and Deep are reviewed as today.

**The fixed point is `start:`.** `review` takes a fixed point as its first word and defaults to the merge-base with the default branch. On main that is `HEAD`, so there would be nothing to review. `flow` records `HEAD` before the first edit and hands it over, so `review`'s own text needs no change.

**Assumptions go in the commit body.** In `pr` mode the PR body carries them for the reader at merge time. With no PR, the commit message is the one place that survives in the log, and the Done report in the chat carries the rest of the body: What, Why, How to check, Evidence.

**Pull with a rebase, then push.** Another commit may have reached main since the work began; a rebase puts this one on top rather than creating a merge commit. With no remote there is nothing to push to, and the run says so in one line instead of failing.
