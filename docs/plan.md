# plan, in detail

What `devflow:plan` does with Deep work, once `flow` (or a human, by hand) hands it a
request. The short version is in the [README](../README.md); `flow`'s own detail is in
[docs/flow.md](flow.md).

## Where a Deep plan goes

Deep work writes its plan into the project, at `.devflow/plans/<short-name>.md`, or as a
GitHub issue when the project's `## Plans` block says so. The plan holds the assumptions
it took. It also holds the pieces to build. Each piece says whether it depends on another
piece, the command that proves it, and a `Done when:` line — the state that means the
piece is finished. That last line is there because whoever builds the piece may have
nobody to ask.

That file is the spec, not a progress tracker. Its job is to hold the assumptions and the
pieces. It is also what `review`'s second axis judges the work against.

**A plan is resumable. The record is `git log`, not the file.** `build` commits each piece
as it goes green. So you can `/clear` between pieces and pick up from the plan plus the
log. The plan says what the pieces are. The log says which of them exist.

Nothing has to remember to tick a box. That is the reason to trust it. That is also why the
checkbox version did not survive.

## Revising a plan

A revise only ever touches a piece with no commit in the log yet. A piece already built is
a piece the plan can no longer quietly disagree with — the commit is the record of what
shipped, and a plan edited under it would drift from that record with nothing to say so.
So a change to a built piece becomes a new piece instead, appended after it.

Every revise leaves a trace: one line under `## Changes`, dated, saying what changed and
why. `spec-reviewer` reads the plan as the spec Standard and Quick work does not get, and a
plan that silently changed shape mid-build would read as consistent when it was not. The
`## Changes` line is what lets a reviewer — human or agent — see the plan moved, and why,
rather than discovering it by diffing two versions nobody was asked to compare. The idea
of tracking a plan's own change history this way, distinct from the build log that tracks
which pieces exist, is the same shape as superpowers' `executing-plans` skill.

## Research before the pieces

A new plan answers what it does not yet know before it writes the pieces. One
`researcher` agent takes one open question — what the repo has now, how others solve it,
what an API really does — at most 3, often just 1, and none when the repo and the round of
questions already answer everything. What comes back lands in the plan as `## Findings`,
every line naming its source, a file and line or a URL.

`flow` researches too, during its rounds, and hands what came back to `plan` as `findings:`.
`plan` writes those lines in word for word and does not research a question `flow` already
did. It researches only what the answers opened up, and a plan started by hand keeps all of
its own research, since no `flow` ran before it. The cap is 3 for each step, so 6 at most in a
run. It is not higher because the cap is what makes the agent merge and drop questions: more
than 3 open questions usually means some are decisions, and a higher number would let them
all through.

Why it is there: every piece trusts the plan, and up to 4 chains build from it at once, so
one wrong fact feeds up to 4 builders. A finding that names its source can be checked.
`spec-reviewer` holds built code against it, and calls code that goes against a finding
built wrong, without reopening the sources.

Why Sonnet and not Haiku: a cheaper model needs evidence first. That is this repo's rule
for a weaker model — "One builder per chain" below names it, and
[docs/provenance.md](provenance.md) keeps it as "deliberately later, with evidence" — and
it bites harder here than on a builder, because the researcher's
output is a fact other agents then build on. Haiku can be tried later with an eval. Until
one says it is safe, Sonnet.

Why Deep work only: Quick and Standard have no plan to put findings in, and #84 just cut
what a Quick job loads. A step every job paid for would undo that. Research is Deep work
only, and on a new plan only: a resume skips it because the plan already holds its
findings, and a revise runs it only when the revise brings a new open question.

The star rule: research may read any source, because a small repo can be right. Anything
copied is always credited with its license. The 1,000-star bar applies only to naming a
repo as evidence of weight — a "known pattern" — or as a foundation in
[docs/provenance.md](provenance.md). It used to bar reading as well, which cost answers
and bought nothing: a source's stars say how many people trust it, not whether it answers
the question.

## One builder per chain

The session that wrote the plan does not build it. The plan groups its pieces into
**chains** — pieces that depend on each other, built in order — and each chain goes to a
fresh `builder` agent. The chains run at the same time, each in its own git worktree, on
its own branch.

The reason is the window. One session building every piece is full of piece 1 by the time
piece 4 starts. Then compaction keeps a summary and drops the plan. With a builder per
chain, the session holds the plan, one `branch:` line per chain, and five lines per piece:
`piece`, `test`, `commit`, `seam`, `stuck`.

The builder gets three things: the plan body pasted in full, the chain letter, and whether
the tree is dirty. It runs the `build` skill on that chain's pieces in order, commits each
one, and reports. It cannot ask you anything. So each piece carries a `Done when:` line,
which is where it stops. If a seam was unclear, it says which one it picked. If it fails
three times, or hits a design decision the plan did not make, it says `stuck`, and that
ends the chain — `plan` stops the job and hands it to you. If a piece is done but the
builder has a doubt, it says so, and the doubt lands in the PR under Assumptions.

Never two builders on one branch. That is what the worktrees are for. When every chain has
reported, `plan` merges the chain branches into your feature branch itself, then removes
the worktrees and the branches.

On a harness that only starts agents when you ask, `plan` asks once for the whole job. Say
no, and it builds every piece in the session, as it did before. Nothing is lost but the
window.

Quick and Standard do not go through any of this — one piece, one session, straight
through `build`, as `flow` always ran them.

Commit the plan file or ignore it, as you prefer. devflow does not add it to `.gitignore`.
It does not expect it there either.

## Chains and worktrees

A Deep run of eight pieces took 43 minutes. Six of them did not depend on each other. They
were built one after another anyway, because the rule was one builder at a time — and that
rule was right about the danger and wrong about the unit.

**Chains, not pieces.** The danger was never two builders; it was two builders committing
to one branch. Pieces that depend on each other still have to be built in order, so those
stay together in a chain and one builder takes the whole chain. What is left between
chains is genuine independence, and that is what runs at the same time. Handing out single
pieces instead would start a builder on work whose predecessor is not in yet.

**A worktree per builder.** `isolation: "worktree"` on the Agent call that spawns a builder
has the harness cut it its own checkout on its own branch. It is asked for per spawn, not
pinned in `agents/builder.md`, so the sequential path can spawn the same builder without
one; pinned, it could not be switched off, and the fallback would still cut worktrees from
the default branch. That is what makes "never two builders on one branch" survive four
builders at once: they share no branch, no working tree and no index. It also means a
builder cannot see the main tree's untracked plan file, which is why the plan body is
pasted in rather than handed over as a path.

**The harness owns the worktree, and it says so in writing.** Anthropic's Claude Code
worktrees documentation is the source for the mechanics here: Claude Code takes a
`git worktree lock` on a subagent's worktree while that agent runs and releases it when
the agent finishes, and a worktree still holding changes stays on disk afterwards until a
periodic sweep clears it. So a builder never removes or prunes a worktree — it would be
fighting the lock, and `prune` reaches every other chain's checkout as well as its own.
Cleanup is `plan`'s, after the merge. The checkouts land under `.claude/worktrees/`, which
this repo's `.gitignore` lists: an unignored one is a second copy of the whole repo
arriving as untracked files, and `submit` stages what is in front of it.

**devflow writes one setting on your machine, and tells you.** The same documentation says
a subagent's worktree branches from the repository's *default* branch unless
`worktree.baseRef` is `"head"` — so on a branch stacked on another PR, every chain would be
cut from `main` and quietly lose its base. `plan` checks `.claude/settings.local.json`,
`.claude/settings.json` and `~/.claude/settings.json`, and if none of them says `"head"` it
merges `{"worktree": {"baseRef": "head"}}` into `.claude/settings.local.json` — the
uncommitted one, never the committed one — keeping everything already in the file. Then it
prints one line saying it did. **That was your call, taken against the recommendation**,
which was that this check only check and `setup` offer to write it: a skill that edits
your settings is doing something you did not ask for in that turn. The line exists because
of that. It also names the side effect, which is real and is not about chains: `--worktree`
sessions *you* start afterwards branch from `HEAD` too, rather than from the default
branch. If the write fails, `plan` says why and falls back to building in order.

**The run that writes it does not get to use it.** Settings are read when a session
starts, so the one `plan` wrote a minute ago is not in force in the session that wrote it —
spawning chains anyway would cut every worktree from the default branch and cost you a
whole job's work to rebuild after a restart. So a run that had to write the file prints
`– **chains** worktree.baseRef was just written — this run does not spawn chains` and
builds that job sequentially, one chain at a time on your branch, spawning each builder
without a worktree; the chains start from your next session.

**The base is a tag, not a memory.** Before the first chain spawns, `plan` tags the branch
tip, `devflow/<plan>/base`, and every chain branch is checked against it with
`git merge-base --is-ancestor` before it is merged. A tag survives a `/clear` and a
restart, which a SHA held in the session does not — and the resume is exactly where the
check matters, because the run that started a wrong-base chain stopped and told you to
restart. A resumed session that finds a chain branch not descending from the tag does not
merge it: it says so, leaves the branch for you, and builds that chain again. `plan`
deletes the tag after the last merge.

**A resumed chain can be half done.** A chain that stopped `stuck` on piece 2 of 3 has one
finished commit on its branch and a half-built piece in a worktree the main tree cannot
see. So `plan` counts the commits on the branch against the chain's pieces before it
merges: a whole chain merges, a short one merges what is there and then goes back into the
spawn loop, and the builder skips the pieces it finds in the log. The half-built piece is
the one thing resume does not carry across; `plan` says where it is and starts that piece
over.

**A dirty main tree means one chain runs without a worktree.** Uncommitted work lives in
the main tree, and a worktree is cut from commits, so it would not carry one line of it.
When a resume finds the tree dirty, that chain is spawned without `isolation`, on your
branch, first and alone. The others go parallel after it reports.

**Then it proves the setting took.** Writing it is not the same as it being read — the
setting may only be loaded when a session starts, and the session that wrote it was
already running. So `plan` records your branch's SHA before the first chain spawns, and
when a chain reports its branch it runs
`git merge-base --is-ancestor <that SHA> <chain branch>`. A non-zero exit means the
worktree was cut from the default branch anyway: that chain is **not** merged, the loop
stops, and `plan` tells you to restart the session and run it again to resume. The chain's
worktree and branch stay on disk, so nothing it built is lost. Merging a chain off the
wrong base would bury the mistake under a merge commit, where it stops looking like a
mistake at all.

**Two chains never edit the same file.** That is a rule on the plan, not a hope about the
merge. A piece that has to touch a file another chain owns goes in `chain: final`, which
runs alone after every other chain has merged. A conflict is far cheaper to prevent while
writing the plan than to resolve in a branch nobody was watching.

**`git merge-tree --write-tree` before every merge.** It answers *would this conflict*
without touching the working tree, so a conflict is found before anything is half-merged.
A non-zero exit stops the job and names the two chains and the files. `plan` never resolves
one: a conflict means the one-file-one-chain rule was broken, and that is a fix to the
plan, not a patch buried in a merge commit.

**The merge is local, and it is not a pull request merge.** `plan` merges each chain
branch into your feature branch on your machine, with `git merge --no-ff`, so every chain
leaves one merge commit naming it and the builders' own SHAs stay exactly as they reported
them. The default branch is never touched. `submit` still opens the PR, `ship` is still
the only thing that merges it, and only you can start `ship`.

**Four chains at once.** A cap, not a target. Four is the middle of the working range the
field has settled on for parallel coding agents, and the ceiling is real: each builder is a
full session with a checkout behind it, so a fifth costs more in rate limit and in reports
you have to read than it buys in wall clock. Further chains wait for a slot.

**The builder runs on Sonnet.** That was your call, taken against this plugin's own "a
cheaper model needs evidence first" line. Four builders at once multiplies the model choice
by four, and the builder's job is the narrowest in the plugin: it is handed a written plan,
one chain and a `Done when:` line, and `build`'s gates decide whether it was done. Effort
stays `high`. It is recorded as a decision rather than a finding, so if plan quality drops
this is the first thing to put back.

**If the harness cannot give a builder a worktree** — no `isolation` option, or the first
spawn with it fails — `plan` says
`– **chains** no worktree isolation — one builder at a time on this branch` once, then
builds one chain at a time on your branch, spawning each builder without `isolation`, with
no merge step and no cleanup. The builder's inputs and report do not change; its `branch:`
line just names your branch. You lose the wall-clock time and nothing else.

## Plans on GitHub

A project can keep its Deep plans as issues instead of files. `setup` asks once and
writes:

```markdown
## Plans
- Tracker: github
```

No block, or `local`, means the file. Then:

- `plan` opens an issue with the label `devflow:plan`. The plan is the body. It prints
  `✓ **plan** #45` on its own line.
- `plan` resumes from it after a `/clear`. `flow`'s step 0b checks for one only when
  commits are ahead, so a typo fix never touches the network.
- `review` reads it as the spec, before any file.
- `submit` adds `Closes #45`. The plan closes when the work merges.
- `build` never reads the tracker. `plan` hands it the piece.

Two costs, and `setup` says both out loud. A cloud session does not have `gh` until its
setup script installs it, and without it a run there falls back to `curl`, then to a file
if that fails too, and says so. And anyone who can edit the issue can edit the plan. A plan
is an order to `build`.

Local and GitHub only. A Linear or Jira ticket is still pasted in as the request.

## Writing every part of the request into a piece

Before the plan is shown, each part of the request has to map to a piece — and a part with
no piece has to get one. A plan that quietly drops something the human asked for reads as
finished when it is not, and nothing downstream would catch it: `build`'s gates check that
each piece does what it says, not that the pieces together cover the request. This
coverage check, done the other way round from how a plan is normally read, is the same
shape as superpowers' `writing-plans` skill.

## Started by hand

`/devflow:plan` run directly — without `flow` — does its own version of `flow`'s step 0b
match check first: a file under `.devflow/plans/`, or an open `devflow:plan` issue whose
subject matches. Then it asks its rounds of questions, using `flow`'s own rules rather
than a second copy of them, writes the plan or the revision, and **stops**. It does not run
the chains — only `flow` sizes the work, checks the folder, and calls `submit` when they
are done, so the by-hand path prints the plan's number or path and the `/devflow:flow`
command that builds it, and leaves the building to a run that does.

That command has to work on a fresh branch. `flow`'s step 0b looks up plan issues only
when commits are ahead, and a plan written by hand has none, so a request that *names* a
plan — `#45` labelled `devflow:plan`, or a path under `.devflow/plans/` — is that plan
whatever the count says. And because no `build` runs in a Deep session, `plan` cuts the
feature branch itself before it tags the base; otherwise the chains would merge into
whatever branch the session stood on, the default one included.

Once it stands on that branch, `plan` writes `Branch: <name>` into the plan, and that is
the one thing `flow` checks to tell a named plan's resume from new work. It used to check
for any `devflow/*/base` tag. Tags are shared by every worktree, and one stays behind when
a run stops, so another plan's tag made a new plan look started (#67). The sequential path
makes no tag at all, and commits nothing until a piece is done, so a plan stuck on piece 1
looked new and its half-built piece was left behind (#68). The line names this plan's own
branch, and it is written on every path, before the first builder runs.

## The reasons, step by step

Every paragraph below was moved here out of `skills/plan/SKILL.md`, word for word, or out
of `skills/flow/SKILL.md` where the text used to live before #64 split this skill out. The
skill holds the steps; this holds why they are what they are.

### Resuming a plan

That is the whole point of writing the plan into the project: a Deep job is long enough to
outlive the context that started it, and `/clear` between pieces is a supported move, not
a failure. But nothing resumes by itself. Arrive here without looking and you write a
second plan over the first, re-ask questions the human already answered, and rebuild
pieces that are already committed.

### Writing the plan down

`submit` reads it to close the issue, and you read it back after a `/clear`.

Whoever builds the piece may have no session to ask, so the plan has to say where the piece
stops.

### One builder per chain

One session building every piece fills its own window with piece 1 by the time piece 4
starts, and then compaction keeps a summary and drops the plan.

The plan holds everything a piece needs, and that is the test of whether the plan is good.

Printing it is not what keeps it: the builder also wrote it as a `Concern:` line in the
piece's commit body, which is what `submit` reads into the PR's **Assumptions** after any
`/clear`.

Two builders committing to one branch at once is a merge conflict nobody is there to solve,
and a piece that depends on the one before it cannot start until that one is in. Chains
keep both of those true while still running in parallel: dependent pieces stay in order
inside one chain, and every chain gets a worktree and a branch of its own, so no two
builders ever share one.

The line says the side effect out loud because there is one, and it is not only about
chains: every `--worktree` session the human starts afterwards branches from `HEAD` too.
Changing a machine's settings quietly is worse than the sentence it costs to say it.

That costs the job its wall-clock time, and it is far cheaper than the
alternative, which is every chain rebuilt off the wrong base after a restart.

Writing the setting is not proof it took: it may only be read when a session starts, and
this session started before you wrote it. Step 2 below checks the result instead of
trusting it, and that tag is what it checks against — on this run, and on a resumed one
that no longer remembers the SHA.

Spawning chains from the wrong base is the failure this whole step exists to avoid, so
falling back is the safe answer, not a lesser one.

**This merge is local**, into the feature branch, on this machine. It is not a pull request
merge and it never touches the default branch, so what `submit` and `ship` promise is
unchanged.

### Check the pieces against the todo

`flow` hands `plan` the todo block the human approved on Deep, and `plan` checks its pieces
against it before the first builder (#94). For one commit the pieces were a second stop of
their own. The human chose the todo as the one approval instead: it says what changes in
their words, where a piece name is for the builder, and now that `flow` researches during
its rounds (#92) the todo is no longer a guess. A plan can still drift from it, since research
inside `plan` can find something new, so a drift — a row added, dropped or changed — shows
the new todo and waits for go again. A match shows the pieces and goes on. A resume does
not stop, because it was approved when it was written, and the by-hand path already stops
after writing.
