# flow, in detail

What `flow` does after the size is announced. The short version is in the [README](../README.md).

## Changing the PR after you have looked at it

`submit` stops at the pull request. You read it and want something different. Go back through `flow`.

`flow` checks the branch first. It sees the open PR. It treats the request as a **follow-up**. Same branch, same PR. `submit` **updates** it instead of opening a second one.

Follow-up mode reads before it asks. The PR's **Assumptions** and the plan file already hold what you decided the first time. So you are only asked what is genuinely new.

Sizing still runs. A follow-up can be anything from a typo to a rethink. The danger list still applies.

Maybe the thing you want changed is something the **PR itself is reporting**. A check went red. A reviewer asked for something. Then `flow` hands it to `tend` instead of taking it into `build`.

Not every failure a pull request reports belongs to that pull request. `tend` is the step that asks whose it is, before it pushes anything.

The request may turn out to be new work rather than a change to that PR. Then `flow` says so and starts a fresh branch. If a harness pins the branch, it cannot. Then it asks you which you meant.

## Where a Deep plan goes, and who builds it

`flow` sizes the work and asks its rounds of questions, then Deep work is
`devflow:plan`'s from there — writing the plan, running one builder per chain, and
reporting back so `flow` can call `submit`. See [docs/plan.md](plan.md) for all of it: the
plan's shape, the chains, the worktrees, resuming after a `/clear`, and plans kept as
GitHub issues.

## The folder the session is standing in

The worktrees below are the builders'. This one is yours, and it is a different problem with the same answer.

**`git checkout -b` moves the whole folder.** `build` cuts the feature branch that way, so two sessions open on one checkout are two sessions sharing one branch pointer. The second to start new work takes it, and the first finds its branch changed underneath it mid-build, with nothing said. **Size has nothing to do with it.** A Quick typo fix moves the folder exactly as a Deep job does, which is why the guard is not a property of the size table.

**Step 0c is the guard, and it asks about the folder rather than about you.** There is no reliable way to ask git whether another session is live, and guessing at one would be a check that is wrong in both directions. So `flow` asks the two things git does answer. Already in a linked worktree — `git rev-parse --path-format=absolute --git-dir --git-common-dir`, and the two answers differ — means this folder holds one session by construction, and nothing changes. On the default branch means the folder is parked where new work is cut from, and nothing changes. **It compares commits, not names.** A detached folder prints `HEAD` on the `Branch` line, which never matches the default branch's name, so the first version called a folder detached at the tip of `origin/main` somebody's work and took a worktree — yet that is exactly how a session parks when another worktree holds `main`. Seen 1 Oct 2026, filed as #76. That fix asked for the exact tip, and the exact tip goes stale: `ship` parks a folder with `git checkout --detach <default branch ref>`, remote-tracking refs are shared by every worktree, and the next fetch anywhere — `ship` step 3, `tend` — moves `origin/main` on. The folder nobody is in then took a worktree it did not need, or, with no **EnterWorktree**, stopped the run (#79). So a clean detached HEAD — `git status --porcelain` prints nothing — now counts as on the default branch in two ways: it is still exactly the tip, or `git merge-base --is-ancestor HEAD <default branch ref>` says the default branch already contains it and `git reflog -1 --format=%gs HEAD` ends `to <default branch ref>`. **The reflog is what tells parked from moved back.** Ancestor-and-clean alone also matches a folder somebody took back on purpose — a `git bisect`, or `git checkout <old sha>` to reproduce a bug — and `build` would move it out from under them. The review of #79 caught that. Parking writes `checkout: moving from <x> to origin/main`; a bisect writes a hash, and a hand checkout writes the hash or `HEAD~3` it was given. **A bisect can still write the parking line.** A human bisecting who runs `git checkout origin/main` to retest the tip leaves `to origin/main` in the reflog, and after the next fetch that commit is behind the tip and still an ancestor, so the folder read as parked and `build` cut a branch mid-bisect. Found by round 2 of the review of #79, filed as #82. Git keeps `BISECT_START` in the folder's own git dir — `git rev-parse --git-path BISECT_START` names it, per worktree — from `git bisect start` until `git bisect reset`, so a detached folder where that file exists is never parked, at the tip or behind it. **The exact tip needs no reflog.** A folder at the tip by hash — `git bisect reset` from a parked folder writes the hash — failed the reflog test in the first draft, and checking out the ref again could not repair it, because git writes no reflog entry when the commit does not change. Round 2 of the review caught it. A folder behind the tip with no reflog, or one that got there some other way, takes a worktree: the cost of a wrong "no" is a worktree, and the cost of a wrong "yes" is somebody's folder moved. A detached HEAD anywhere else is somebody's work, the same as a named branch. **Behind the tip, `build` has to hear "new work".** Its own rule cuts a branch where a detached HEAD stands, and that is now a stale commit, so step 0c tells it to cut from the ref. Only a folder that is *neither* is a folder parked on somebody's work, and that is the one case that takes a worktree of its own, through the **EnterWorktree** tool.

**It is narrower than `ship`'s idea of a free folder, on purpose.** `ship`'s deploy step counts any clean detached folder as free and moves it to the ref. `flow` asks for the default branch to contain the commit as well. A clean detached HEAD on a commit `main` does not have is either somebody's experiment or commits made with no branch, and `build`'s `checkout -b` would carry them into the new PR. `ship` moves the folder and builds nothing on it, so it is not carrying anything forward.

**A linked worktree settles the folder, not the branch it stands on.** With `worktree.baseRef` at `head`, a chip session or a `claude --worktree` session is cut from whatever the main checkout was on. If that was a feature branch, the worktree's branch is ahead of the default branch with no PR, `build` keeps it, and the new PR carries the other feature's commits. So for new work, a worktree whose `Commits ahead` is above `0` has `build` cut from the default branch ref, with a `✓ **worktree** <branch> carries commits` line. `unknown` is not a count, only a missing `origin/HEAD`, so step 0c finds the default through `git remote show origin` and counts itself; with no `origin` at all there is nothing to cut from, and the worktree keeps its branch. The commits stay on that branch; they are just not carried into the new PR. **It does not ask where the commits came from.** The first version did, with `git branch --contains HEAD`, and kept the branch when no other branch held them. The review caught that `git branch` sees local branches only, and `ship` deletes the local branch after a squash or rebase merge, so borrowed commits then read as the worktree's own and ship a second time. And the answer never mattered: step 0c only runs for new work, so the commits predate the request either way. That is also what a plain checkout does — a folder ahead of the default branch with no PR gets its new work cut from the default branch too. The gap was found on 23 Sep 2026 by reading the chip path, not by a failed run.

**It is deliberately conservative, and the escape is one command.** A folder sitting on an old feature branch gets a worktree even when you are alone in it, because "alone" is the part `flow` cannot see. `git checkout main` before you start puts the folder back on the default branch and step 0c goes quiet.

**The skill says out loud that it is the instruction.** `EnterWorktree`'s own description says to reach for a worktree only when the human or the project asked for one. A skill that quietly assumed it counted would be refused at the moment it fired, on the one path where being refused is expensive — so step 0c states it, in the text, where the model reads it.

**`--path-format=absolute` is load-bearing, and it was not there first.** Asked for bare, git answers `--git-common-dir` relative to the current directory: from `docs/` in a plain checkout it prints `../.git` against an absolute `--git-dir`. Step 0c reads two different answers as "already in a worktree" and waves the folder through, so the guard did nothing at all for any session started below the repo root — and said nothing while not doing it. The review of 22 Sep 2026 caught it before the first PR; `skills/test-frontmatter.py` now pins the absence of the bare form beside the presence of the working one.

**A worktree settles the folder, not the base.** `worktree.baseRef` is `head` on any machine where `plan` has written it for the chains, so the new checkout comes off the branch the folder happened to be on — the very work this request has nothing to do with. Step 0c does not touch that setting; it hands `build` the same "new work, fresh branch cut from the default branch ref" it always did, and `build`'s `checkout -b` fixes the base inside a folder where it reaches nobody.

**The branch the worktree opens on is the trap inside the fix.** `EnterWorktree` makes its own branch, named after the worktree and cut from `HEAD` — which at this point in the step is always somebody else's branch. It looks deliberate, and `build`'s own rule is *already on a branch, keep it, whatever it is called*, so a session that reads it as the feature branch stops there and nothing downstream catches it: the pull request simply carries the parked branch's commits. That is the failure step 0 refuses on a stale branch, arriving by a different door. So step 0c names the branch as not-the-feature-branch and prints what is still owed, rather than leaving the re-cut implied — a step that prints something has done something, and a step that implies it has not.

**How that got into the skill is worth keeping.** The eval case scored 1 of 3 on its first paid run, and the reading taken from it was that sessions were keeping this branch. That was a guess. The real cause was the case's own `max_turns: 10` cutting runs off before the branch was cut at all, and raising it to 20 gave 3 of 3 against the *unchanged* rule. The trap is real on its own reading of `build`, so it stays named — but it was never the thing the eval measured, and the run is what said so. `evals/README.md` carries the general lesson.

**The fallback does not branch anyway.** No `EnterWorktree` in the harness, or a call that fails or is refused, ends the run with `✗ **worktree** refused — this folder belongs to <branch>. Start again with: claude --worktree`. Carrying on is the exact outcome the step exists to prevent, so there is no path through it that ends in `checkout -b` on a folder somebody else is using.

## One feature per run

One flow run ends as one PR. A request that names three features would end as one PR carrying three things, or as a plan that mixes them, so `flow` splits before it sizes anything.

**Default is do not split.** A feature is something that could ship alone and that a user would ask for in its own sentence. Parts that depend on each other are one feature, not several — splitting those would hand `build` a piece that cannot pass on its own. And a request that already says how it wants to be built — "each as its own piece", "in one PR" — is one feature with pieces, not several features: the human shaped it, and its pieces belong to the plan, not the backlog.

The question comes before the size line, not after, because sizing needs to know which feature it is sizing. Ask first, size the one kept feature second, and the size line means what it says.

The rest are parked, never dropped. A project whose `## Plans` block says `github` gets one issue per parked feature, labelled `devflow:backlog` — `setup` makes that label alongside `devflow:plan`, and `flow` makes it too if a project set up before this existed. Everything else — no block, `local`, or `gh` failing on the day — writes one file per parked feature at `.devflow/backlog/<short-name>.md` instead.

A later run given `.devflow/backlog/<name>.md` as its request reads the file as the request and deletes it in the same branch, so the deletion ships with the PR that finally builds it. Nothing lingers to be parked twice.

**In the desktop app, each parked feature also gets a chip.** Parking alone left the human to type `/devflow:flow .devflow/backlog/x.md` by hand for each one. The app's `spawn_task` tool puts a chip in front of them instead, and one click starts that feature in its own session. A chip is a shortcut to the record, never the record: it exists only in the app, and it is gone once dismissed, so parking runs first and runs everywhere. Where the tool does not exist, nothing is offered and nothing is printed.

**The chip never points at the backlog file.** A chip session starts in a fresh worktree, and a worktree is cut from commits. The backlog file stays untracked until the kept feature's PR commits it, so a chip that said "run `.devflow/backlog/x.md`" would start a run with no request. So an issue gets `/devflow:flow #<n>`, and a file gets the feature's own text, plus one line asking the new run to delete the file if its checkout has it.

**A chip clicked before the kept PR merges finds no file**, and the kept PR commits that file to the default branch afterwards: an entry for a feature that already shipped. The first version had the chip run name the file under **Known issues**, but `submit` rebuilds that section from review, so the note could vanish, and a later run on the file would build the feature twice. Two other fixes were weighed and dropped. The kept run leaving the file uncommitted loses the feature when the chip is dismissed, because then the chip is the only record. The chip run checking `.devflow/backlog/` finds nothing, because the file is not in its worktree yet — that is the whole problem.

So the chip run leaves a mark that outlives both orders of merging: `submit` ends its commit body with `Backlog: .devflow/backlog/<name>.md`, and puts the same line in the PR body, whether or not the file was there. Step 1 looks for that line before it builds a backlog file — the default branch's log first, which needs no network, then the merged PRs, which catch a Deep branch with nothing left for `submit` to commit and a squash that kept only the PR body. A hit deletes the file and builds nothing, which is why step 1b never parks under a name an old `Backlog:` line already holds: a new feature reusing that name would read as built. The PR search is filtered with `--jq` on the exact line, because GitHub's phrase search is loose: a quoted phrase from #34's body matched four PRs that do not contain it.

**Only text the human typed goes into a file-case chip.** A chip prompt reaches the next run as free text, which step 1 reads as the human's own words. Text parked from an issue body or a backlog file was never that, and step 1 guards it for a reason. So that text gets no file-case chip; the file stays the record, and a later run reads it through the guard.

## The project's words

Some things outlive one job. What this project means by *session*. Or *account*.

They go in a `## Words` block in `CONTEXT.md`, at the project root.

```markdown
## Words
- **Session** — one agent run, start to finish. The browser kind is a *login*.
```

`flow` writes a line there when your answer settles a word. It tells you in one line. Next job, `flow` and `build` read it. Your words show up in the questions, the test names and the commits.

Three rules keep it small and true:

- **Only words you settled.** Never a word the plugin picked itself.
- **Meaning only.** No file paths, no function names. Those rot. A meaning does not.
- **Lazily.** No settled word, no file. `setup` does not create it.

`build` reads it and never writes it. `build` reports a wrong word to you. It does not fix it in silence.

`review` does not get it. `reviewer` must name an input that fails. A bad word cannot fail an input. Give it a style guide and it starts reporting style.

## If it sizes something wrong

```
/devflow:flow --deep <request>
/devflow:flow --quick <request>
```

`flow` records overrides through `devflow:lesson`, as a devflow `mistake`, and `lesson` writes it into the lessons repo, not into this project or `~/.claude`. They are notes about this plugin, not about any one repo, which is why they go there rather than anywhere per-project.

`flow` also prints the line it always did.

Each line is a real example of the classifier getting it wrong, with your correction. Because the destination is a repo rather than a file under `~/.claude`, it survives a hosted session ending — see [docs/lessons.md](lessons.md) for why that mattered, and for the review step that reads it later.

## The reasons, step by step

Every paragraph below was moved here out of `skills/flow/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

### The Context block

**Every injected line above is a single command on purpose.** An injected command
that Claude Code cannot statically analyse fails its permission check, and a failed
injection **aborts the whole skill** — Claude never sees one word of this file. Shell
control flow does it: `if ... fi`, and `x=$(...)` capture. A `||` fallback and a single
pipe are fine, which is why every line here is shaped that way. Do not compress these
back into one clever line; the branching belongs below, where the model does it.

### Step 0 — is this a follow-up?

`flow` runs on every change, including the typo fixes it is tuned for, and a round-trip on
all of them to answer a question git already settled is a poor trade.

Asking again for something the human has already told you is the interruption this plugin
exists to avoid.

That is the whole reason `tend` exists: not every failure a pull request reports belongs to
the pull request, and a fix pushed for a failure nobody attributed is worse than no fix.
`tend` reads what is actually red, decides whose it is, and comes back through `build` and
`submit` itself. You would be routing around the one step that stops the mistake.

Nothing downstream will create it for you: `build` keeps whatever branch it finds, and
`submit` only guards the default one, so work you called new lands on the old branch and
`submit` folds it into the pull request that is already open — the one thing this step
exists to prevent.

The colon after `{owner}` is written `%3A` on purpose: `gh` reads a bare `:repo`,
`:owner` or `:branch` as an old placeholder, and a branch named `repo-cleanup` then
matches every PR in the repo.

### Step 0b — is this plan already running?

A Deep job is long enough to outlive the context that started it, and `/clear` between
pieces is a supported move, not a failure. But nothing resumes by itself: arrive here
without looking and you write a second plan over the first, re-ask questions the human
already answered, and rebuild pieces that are already committed. `flow` only checks
whether a plan matches — resuming it, and everything past that, is `devflow:plan`'s job;
see [docs/plan.md](plan.md).

A plan named in the request has started when a piece is in the log or its own `Branch:`
line names a branch that exists. Not any plan's base tag: those are shared by every
worktree and outlive a stopped run, and the sequential path never makes one. A started plan
on another branch stops the run rather than resuming on the wrong commits.

### Step 0c — is this folder yours to branch in?

That is not a small difference: `build`'s own rule is *already on a branch, keep it, whatever it
is called*, so nothing downstream will catch it, and the pull request ends up carrying
`<branch>`'s commits. Step 0 refuses that on a stale branch, and this step refuses it here.

### Step 1 — get the request

Anyone can open an issue, and you cannot tell from here who did.

A number you could not open is not a request, and sizing one you guessed at is worse than
asking.

### Step 3 — a tracker action is a todo row

A request that says "close #53 as not planned, with a comment" asks for something no diff
holds. Listed as its own `todo` row it is on screen before anything runs, and `submit`
does it once the PR is open (#77). One that came from an issue body is asked about first,
even on Quick, for the reason step 1 gives: anyone can open an issue, and closing or
commenting is public.

### Step 3 — Standard and Deep wait for go

Standard used to print its `todo` block and go straight on, so the human saw what would
be done only while it was being done (#94). A wrong guess on Standard is a whole build
thrown away, not a typo, so Standard now waits for go, as Deep does. When Standard has
questions, answering them is the go, so it still stops once. Quick does not wait: a stop
on a one-line fix costs more than it saves, and the block is still on screen above the
work. The `see` line is there because `todo` lines name the work, not what it does: it is
the one line that says what the user will notice.

The block was plain `→` lines at first, and the human found they did not stand out: they
looked like every other line of the run. So the changes are a table under the `todo` line,
and `plan`'s pieces are a table under the `pieces` line. A table alone still did not stand
out, so each block sits in a quote box. The shaped line stays at the top of each box, so
each box still opens with a line of the usual shape. A line that waits — the `todo` line on
Standard and Deep, and `plan`'s drift line — ends `— waiting for your go`, and `submit`'s
recap repeats it without those words, because by then the go came. The pieces line does
not wait, so it never says it does.

### Step 1b — one feature per run

A request that names more than one feature is split before it is sized, because sizing
needs to already know which feature it is sizing. Default is do not split — a feature is
whatever a user would ask for in its own sentence, and parts that depend on each other are
one feature, not several. The parked ones go to a GitHub issue labelled `devflow:backlog`
when the project keeps its plans there, or a file under `.devflow/backlog/` otherwise, so
nothing named in the request is silently dropped.

### Step 4 — the project's words

This is the one file devflow writes that a later run reads. A plan is for one job.
`CONTEXT.md` outlives the job.

### Step 4 — asking questions

`flow` asks in popups, with the `AskUserQuestion` tool. A round is up to 4 questions, the
tool's own limit, shown one at a time, each with 2 to 4 options and the recommended one
first, labelled "(Recommended)". The tool adds "Other" itself. Rounds go on until no open
question could change a todo line, a plan piece, or what the user sees, and there is no cap on them: a later
round holds only what the earlier answers opened up, so a question whose premise is not
settled waits for the answer that settles it instead of taking its recommendation. Standard
asks the same way, only when something is genuinely unclear, and Quick asks nothing. On
Deep the `todo` block is printed above the popup, and answering the popup approves it, as
`yes to all` used to; Other is how you change it. Answer a question with "explain this" and
you get it in plain words, then that one question again. Where there is no popup tool —
evals, `claude -p` — it falls back to the numbered list with a recommendation on each, and
`yes to all` still works there.

It used to ask a single numbered list, with one more list on Deep for a held question. A held
question now waits for the round its answer opens instead of taking its recommendation, so
the stop rule moved from a count to a test: would any answer change the build.

The test first read "a todo line or a plan piece", and that was too coarse. The error text,
or what happens on empty input, changes neither, so those questions were skipped into
**Assumptions** and seen only at merge. The human widened it to what the user sees.

The human answers from memory. The code cannot be wrong about itself.

This is also what makes `yes to all` safe. A recommendation on a decision is an opinion. A
recommendation on a fact is a guess. A guess lands in **Assumptions** and looks like a
decision.

More than two is a design session, not a change.

Question 2 shows the split. "Per-user or global" is a decision, so it is asked. "How
notifications store it" is a fact, so it was looked up and handed over.

### Step 4 — Deep calls devflow:plan

Writing the plan, one builder per chain, and everything past the rounds of questions is
`devflow:plan`'s job now, not this skill's — see [docs/plan.md](plan.md) for why its rules
are what they are.

### Step 5 — submit it

`submit` passes it to `review`, and `review`'s second axis judges the change against it.

Standard work has no plan, so the words the human typed are the only spec there is — and
until this line existed, nobody read them again after step 1.

`build` deliberately does not know about submitting, so if you do not make this call nobody
does, and the work sits finished-but-uncommitted on a dirty working tree.

### Recording overrides

If the human used `--quick` or `--deep`, they are correcting a mistake this skill would
have made. That is free labelled test data and it should not be lost.

It goes through `devflow:lesson` rather than a file `flow` writes itself, and lands in the
lessons repo rather than anywhere per-project. Kept per-project these would scatter across
every repo you work in, get committed into unrelated projects, and be impossible to review
together — which is the only way they are useful. One shared collector, used by every
skill with a clear sign to record, is cheaper than each skill inventing its own file and
its own review step. See [docs/lessons.md](lessons.md) for the fuller reasoning.

On a hosted session — Claude Code on the web included — `~/.claude` is inside a container
that is deleted when the session ends, which is exactly why the destination moved to a
repo. The reply is in the transcript regardless, so it was never the only copy.
