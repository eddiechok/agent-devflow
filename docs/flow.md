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

## Where a Deep plan goes

Deep work writes its plan into the project, at `.devflow/plans/<short-name>.md`. The plan holds the assumptions it took. It also holds the pieces to build. Each piece says whether it depends on another piece, the command that proves it, and a `Done when:` line — the state that means the piece is finished. That last line is there because whoever builds the piece may have nobody to ask.

That file is the spec, not a progress tracker. Its job is to hold the assumptions and the pieces. It is also what `review`'s second axis judges the work against.

**A plan is resumable. The record is `git log`, not the file.** `build` commits each piece as it goes green. So you can `/clear` between pieces and pick up from the plan plus the log. The plan says what the pieces are. The log says which of them exist.

Nothing has to remember to tick a box. That is the reason to trust it. That is also why the checkbox version did not survive.

## One builder per chain

The session that wrote the plan does not build it. The plan groups its pieces into **chains** — pieces that depend on each other, built in order — and each chain goes to a fresh `builder` agent. The chains run at the same time, each in its own git worktree, on its own branch.

The reason is the window. One session building every piece is full of piece 1 by the time piece 4 starts. Then compaction keeps a summary and drops the plan. With a builder per chain, the session holds the plan, one `branch:` line per chain, and five lines per piece: `piece`, `test`, `commit`, `seam`, `stuck`.

The builder gets three things: the plan body pasted in full, the chain letter, and whether the tree is dirty. It runs the `build` skill on that chain's pieces in order, commits each one, and reports. It cannot ask you anything. So each piece carries a `Done when:` line, which is where it stops. If a seam was unclear, it says which one it picked. If it fails three times, or hits a design decision the plan did not make, it says `stuck`, and that ends the chain — `flow` stops the job and hands it to you. If a piece is done but the builder has a doubt, it says so, and the doubt lands in the PR under Assumptions.

Never two builders on one branch. That is what the worktrees are for. When every chain has reported, `flow` merges the chain branches into your feature branch itself, then removes the worktrees and the branches.

On a harness that only starts agents when you ask, `flow` asks once for the whole job. Say no, and it builds every piece in the session, as it did before. Nothing is lost but the window.

Quick and Standard do not change. One piece, one session.

Commit the file or ignore it, as you prefer. devflow does not add it to `.gitignore`. It does not expect it there either.

## Chains and worktrees

A Deep run of eight pieces took 43 minutes. Six of them did not depend on each other. They were built one after another anyway, because the rule was one builder at a time — and that rule was right about the danger and wrong about the unit.

**Chains, not pieces.** The danger was never two builders; it was two builders committing to one branch. Pieces that depend on each other still have to be built in order, so those stay together in a chain and one builder takes the whole chain. What is left between chains is genuine independence, and that is what runs at the same time. Handing out single pieces instead would start a builder on work whose predecessor is not in yet.

**A worktree per builder.** `isolation: worktree` in `agents/builder.md` has the harness cut each builder its own checkout on its own branch. That is what makes "never two builders on one branch" survive four builders at once: they share no branch, no working tree and no index. It also means a builder cannot see the main tree's untracked plan file, which is why the plan body is pasted in rather than handed over as a path.

**The harness owns the worktree, and it says so in writing.** Anthropic's Claude Code worktrees documentation is the source for the mechanics here: Claude Code takes a `git worktree lock` on a subagent's worktree while that agent runs and releases it when the agent finishes, and a worktree still holding changes stays on disk afterwards until a periodic sweep clears it. So a builder never removes or prunes a worktree — it would be fighting the lock, and `prune` reaches every other chain's checkout as well as its own. Cleanup is `flow`'s, after the merge. The checkouts land under `.claude/worktrees/`, which this repo's `.gitignore` lists: an unignored one is a second copy of the whole repo arriving as untracked files, and `submit` stages what is in front of it.

**Two chains never edit the same file.** That is a rule on the plan, not a hope about the merge. A piece that has to touch a file another chain owns goes in `chain: final`, which runs alone after every other chain has merged. A conflict is far cheaper to prevent while writing the plan than to resolve in a branch nobody was watching.

**`git merge-tree --write-tree` before every merge.** It answers *would this conflict* without touching the working tree, so a conflict is found before anything is half-merged. A non-zero exit stops the job and names the two chains and the files. `flow` never resolves one: a conflict means the one-file-one-chain rule was broken, and that is a fix to the plan, not a patch buried in a merge commit.

**The merge is local, and it is not a pull request merge.** `flow` merges each chain branch into your feature branch on your machine, with `git merge --no-ff`, so every chain leaves one merge commit naming it and the builders' own SHAs stay exactly as they reported them. The default branch is never touched. `submit` still opens the PR, `ship` is still the only thing that merges it, and only you can start `ship`.

**Four chains at once.** A cap, not a target. Four is the middle of the working range the field has settled on for parallel coding agents, and the ceiling is real: each builder is a full session with a checkout behind it, so a fifth costs more in rate limit and in reports you have to read than it buys in wall clock. Further chains wait for a slot.

**The builder runs on Sonnet.** That was your call, taken against this plugin's own "a cheaper model needs evidence first" line. Four builders at once multiplies the model choice by four, and the builder's job is the narrowest in the plugin: it is handed a written plan, one chain and a `Done when:` line, and `build`'s gates decide whether it was done. Effort stays `high`. It is recorded as a decision rather than a finding, so if plan quality drops this is the first thing to put back.

**If the harness cannot give a builder a worktree** — no `isolation` option, or the first spawn with it fails — `flow` says `chains in-session: no worktree isolation` once, then builds every piece in order on your branch, as it did before, with no merge step and no cleanup. The `chain:` letters are only an ordering hint in that mode. You lose the wall-clock time and nothing else.

## Plans on GitHub

A project can keep its Deep plans as issues instead of files. `setup` asks once and writes:

```markdown
## Plans
- Tracker: github
```

No block, or `local`, means the file. Then:

- `flow` opens an issue with the label `devflow:plan`. The plan is the body. It prints `plan: #45` on its own line.
- `flow` resumes from it after a `/clear`. Only when commits are ahead, so a typo fix never touches the network.
- `review` reads it as the spec, before any file.
- `submit` adds `Closes #45`. The plan closes when the work merges.
- `build` never reads the tracker. `flow` hands it the piece.

Two costs, and `setup` says both out loud. The web sandbox has no `gh`, so a run there falls back to a file and says so. And anyone who can edit the issue can edit the plan. A plan is an order to `build`.

Local and GitHub only. A Linear or Jira ticket is still pasted in as the request.

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

`flow` records overrides to `~/.claude/devflow/overrides.md`. They go there **globally, not per project**. They are notes about this plugin, not about any one repo. They are only useful when you review them together.

`flow` also prints the line it wrote.

⚠️ On a hosted session that home directory sits inside a container. The container goes away when the session ends. The file does not survive, so the reply is the only copy. Paste it somewhere durable if you work on the web.

Each line is a real example of the classifier getting it wrong, with your correction. After a month you have a set of labelled cases from actual use. That beats any examples invented up front. Do not delete the file.

This is the only self-improvement machinery in Phase 1. It only collects, on purpose. There is no review step yet.

Read the file when it has twenty or so lines in it. See whether a pattern is there. If one is, that is a change to `flow`. Make it through the normal flow, since this repo is just another project.

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

### Step 0b — is this plan already running?

That is the whole point of writing the plan into the project: a Deep job is long enough to
outlive the context that started it, and `/clear` between pieces is a supported move, not
a failure. But nothing resumes by itself. Arrive here without looking and you write a
second plan over the first, re-ask questions the human already answered, and rebuild
pieces that are already committed.

### Step 1 — get the request

Anyone can open an issue, and you cannot tell from here who did.

A number you could not open is not a request, and sizing one you guessed at is worse than
asking.

### Step 4 — the project's words

This is the one file devflow writes that a later run reads. A plan is for one job.
`CONTEXT.md` outlives the job.

### Step 4 — asking questions

The human answers from memory. The code cannot be wrong about itself.

This is also what makes `yes to all` safe. A recommendation on a decision is an opinion. A
recommendation on a fact is a guess. A guess lands in **Assumptions** and looks like a
decision.

More than two is a design session, not a change.

Question 2 shows the split. "Per-user or global" is a decision, so it is asked. "How
notifications store it" is a fact, so it was looked up and handed over.

### Step 4 — writing the plan down

`submit` reads it to close the issue, and you read it back after a `/clear`.

Whoever builds the piece may have no session to ask, so the plan has to say where the piece
stops.

### Step 4 — one builder per chain

One session building every piece fills its own window with piece 1 by the time piece 4
starts, and then compaction keeps a summary and drops the plan.

The plan holds everything a piece needs, and that is the test of whether the plan is good.

Printing it is not what keeps it: the builder also wrote it as a `Concern:` line in the
piece's commit body, which is what `submit` reads into the PR's **Assumptions** after any
`/clear`.

Two builders committing to one branch at once is a merge conflict nobody is there to solve,
and a piece that depends on the one before it cannot start until that one is in. Chains keep
both of those true while still running in parallel: dependent pieces stay in order inside one
chain, and every chain gets a worktree and a branch of its own, so no two builders ever share
one.

### Step 5 — submit it

`submit` passes it to `review`, and `review`'s second axis judges the change against it.

Standard work has no plan, so the words the human typed are the only spec there is — and
until this line existed, nobody read them again after step 1.

`build` deliberately does not know about submitting, so if you do not make this call nobody
does, and the work sits finished-but-uncommitted on a dirty working tree.

### Recording overrides

If the human used `--quick` or `--deep`, they are correcting a mistake this skill would
have made. That is free labelled test data and it should not be lost.

Global on purpose. These are notes about **this plugin**, not about the project you happen
to be in. Kept per-project they would scatter across every repo you work in, get committed
into unrelated projects, and be impossible to review together — which is the only way they
are useful.

On a hosted session — Claude Code on the web included — `~/.claude` is inside a container
that is deleted when the session ends, so the file you just wrote may not be there
tomorrow. The reply is in the transcript, which is.
