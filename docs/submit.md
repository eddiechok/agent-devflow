# submit, in detail

Why `submit`'s steps are what they are. The steps themselves are in
[the skill](../skills/submit/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/submit/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

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

It pins the range, finds the plan or issue if there is one, and runs both axes in fresh agents.

On work with no plan and no issue, that text is the spec the second axis reads, and without it that axis does not run.

### Why round 2 is scoped

That is a range and another agent's report, not this session's reasoning, so `review`'s rule holds. A full re-read of the branch finds the same clean files again at the same price, and the cost of a review should go where the change went.

### Why a truncated review is a finding

A truncated review prints exactly like a clean one, which is the whole reason the line is there; dropping it here is the same failure as dropping `NOT RUN`.

### Why a `Falls` still gets checked

Two agents disagreeing is not a majority vote; it is one of them having read something the other did not, and you are the one who can go and look.

### Why `/code-review` is not here

The built-in `/code-review` is a better review than this one, and it still does not belong here: it works on an **open pull request** and comments back on it, and there is no PR yet. It goes to the human at step 9, where one exists.

## Step 6 — the docs

This step exists because nothing before it reads the docs. `build` tests behaviour and `review` judges the code, so a diagram that stops matching the skill it draws goes stale with no red anywhere. `docs/pipeline.md` did exactly that after the builder-per-piece change, and a human found it later. One read here is cheaper than the drift.

## Step 7 — the commit

A marker removed at 3, a live-check fix at 4, a review fix at 5, a doc at 6 — any of them means step 2's run no longer covers the tree you are about to commit.

The checks and the look both postdate the last edit; that is the whole of the rule, stated at the last place an edit can land.

`build` commits each plan piece as it lands, so the working tree can be clean by the time you reach this step — and the fixes from steps 5 and 6 may be all that is left.

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

`flow` decided it before any code was written, and that decision does not always survive to here — a compaction, a long Deep job, or a `submit` you were invoked into directly all lose it. Losing it is silent, and what it drops is the only security gate in the loop. Deciding twice costs a moment; missing it costs the gate.
