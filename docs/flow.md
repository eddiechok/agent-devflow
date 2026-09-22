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

## The folder the session is standing in

The worktrees below are the builders'. This one is yours, and it is a different problem with the same answer.

**`git checkout -b` moves the whole folder.** `build` cuts the feature branch that way, so two sessions open on one checkout are two sessions sharing one branch pointer. The second to start new work takes it, and the first finds its branch changed underneath it mid-build, with nothing said. **Size has nothing to do with it.** A Quick typo fix moves the folder exactly as a Deep job does, which is why the guard is not a property of the size table.

**Step 0c is the guard, and it asks about the folder rather than about you.** There is no reliable way to ask git whether another session is live, and guessing at one would be a check that is wrong in both directions. So `flow` asks the two things git does answer. Already in a linked worktree — `git rev-parse --path-format=absolute --git-dir --git-common-dir`, and the two answers differ — means this folder holds one session by construction, and nothing changes. On the default branch means the folder is parked where new work is cut from, and nothing changes. Only a folder that is *neither* is a folder parked on somebody's work, and that is the one case that takes a worktree of its own, through the **EnterWorktree** tool.

**It is deliberately conservative, and the escape is one command.** A folder sitting on an old feature branch gets a worktree even when you are alone in it, because "alone" is the part `flow` cannot see. `git checkout main` before you start puts the folder back on the default branch and step 0c goes quiet.

**The skill says out loud that it is the instruction.** `EnterWorktree`'s own description says to reach for a worktree only when the human or the project asked for one. A skill that quietly assumed it counted would be refused at the moment it fired, on the one path where being refused is expensive — so step 0c states it, in the text, where the model reads it.

**`--path-format=absolute` is load-bearing, and it was not there first.** Asked for bare, git answers `--git-common-dir` relative to the current directory: from `docs/` in a plain checkout it prints `../.git` against an absolute `--git-dir`. Step 0c reads two different answers as "already in a worktree" and waves the folder through, so the guard did nothing at all for any session started below the repo root — and said nothing while not doing it. The review of 22 Sep 2026 caught it before the first PR; `skills/test-frontmatter.py` now pins the absence of the bare form beside the presence of the working one.

**A worktree settles the folder, not the base.** `worktree.baseRef` is `head` on any machine where `flow` has written it for the chains, so the new checkout comes off the branch the folder happened to be on — the very work this request has nothing to do with. Step 0c does not touch that setting; it hands `build` the same "new work, fresh branch cut from the default branch ref" it always did, and `build`'s `checkout -b` fixes the base inside a folder where it reaches nobody.

**The fallback does not branch anyway.** No `EnterWorktree` in the harness, or a call that fails or is refused, ends the run with `worktree refused — this folder belongs to <branch>. Start again with: claude --worktree`. Carrying on is the exact outcome the step exists to prevent, so there is no path through it that ends in `checkout -b` on a folder somebody else is using.

## Chains and worktrees

A Deep run of eight pieces took 43 minutes. Six of them did not depend on each other. They were built one after another anyway, because the rule was one builder at a time — and that rule was right about the danger and wrong about the unit.

**Chains, not pieces.** The danger was never two builders; it was two builders committing to one branch. Pieces that depend on each other still have to be built in order, so those stay together in a chain and one builder takes the whole chain. What is left between chains is genuine independence, and that is what runs at the same time. Handing out single pieces instead would start a builder on work whose predecessor is not in yet.

**A worktree per builder.** `isolation: "worktree"` on the Agent call that spawns a builder has the harness cut it its own checkout on its own branch. It is asked for per spawn, not pinned in `agents/builder.md`, so the sequential path can spawn the same builder without one; pinned, it could not be switched off, and the fallback would still cut worktrees from the default branch. That is what makes "never two builders on one branch" survive four builders at once: they share no branch, no working tree and no index. It also means a builder cannot see the main tree's untracked plan file, which is why the plan body is pasted in rather than handed over as a path.

**The harness owns the worktree, and it says so in writing.** Anthropic's Claude Code worktrees documentation is the source for the mechanics here: Claude Code takes a `git worktree lock` on a subagent's worktree while that agent runs and releases it when the agent finishes, and a worktree still holding changes stays on disk afterwards until a periodic sweep clears it. So a builder never removes or prunes a worktree — it would be fighting the lock, and `prune` reaches every other chain's checkout as well as its own. Cleanup is `flow`'s, after the merge. The checkouts land under `.claude/worktrees/`, which this repo's `.gitignore` lists: an unignored one is a second copy of the whole repo arriving as untracked files, and `submit` stages what is in front of it.

**devflow writes one setting on your machine, and tells you.** The same documentation says a subagent's worktree branches from the repository's *default* branch unless `worktree.baseRef` is `"head"` — so on a branch stacked on another PR, every chain would be cut from `main` and quietly lose its base. `flow` checks `.claude/settings.local.json`, `.claude/settings.json` and `~/.claude/settings.json`, and if none of them says `"head"` it merges `{"worktree": {"baseRef": "head"}}` into `.claude/settings.local.json` — the uncommitted one, never the committed one — keeping everything already in the file. Then it prints one line saying it did. **That was your call, taken against the recommendation**, which was that `flow` only check and `setup` offer to write it: a skill that edits your settings is doing something you did not ask for in that turn. The line exists because of that. It also names the side effect, which is real and is not about chains: `--worktree` sessions *you* start afterwards branch from `HEAD` too, rather than from the default branch. If the write fails, `flow` says why and falls back to building in order.

**The run that writes it does not get to use it.** Settings are read when a session starts, so the one `flow` wrote a minute ago is not in force in the session that wrote it — spawning chains anyway would cut every worktree from the default branch and cost you a whole job's work to rebuild after a restart. So a run that had to write the file prints `chains next session: worktree.baseRef was just written` and builds that job sequentially, one chain at a time on your branch, spawning each builder without a worktree; the chains start from your next session.

**The base is a tag, not a memory.** Before the first chain spawns, `flow` tags the branch tip, `devflow/<plan>/base`, and every chain branch is checked against it with `git merge-base --is-ancestor` before it is merged. A tag survives a `/clear` and a restart, which a SHA held in the session does not — and the resume is exactly where the check matters, because the run that started a wrong-base chain stopped and told you to restart. A resumed session that finds a chain branch not descending from the tag does not merge it: it says so, leaves the branch for you, and builds that chain again. `flow` deletes the tag after the last merge.

**A resumed chain can be half done.** A chain that stopped `stuck` on piece 2 of 3 has one finished commit on its branch and a half-built piece in a worktree the main tree cannot see. So `flow` counts the commits on the branch against the chain's pieces before it merges: a whole chain merges, a short one merges what is there and then goes back into the spawn loop, and the builder skips the pieces it finds in the log. The half-built piece is the one thing resume does not carry across; `flow` says where it is and starts that piece over.

**A dirty main tree means one chain runs without a worktree.** Uncommitted work lives in the main tree, and a worktree is cut from commits, so it would not carry one line of it. When a resume finds the tree dirty, that chain is spawned without `isolation`, on your branch, first and alone. The others go parallel after it reports.

**Then it proves the setting took.** Writing it is not the same as it being read — the setting may only be loaded when a session starts, and the session that wrote it was already running. So `flow` records your branch's SHA before the first chain spawns, and when a chain reports its branch it runs `git merge-base --is-ancestor <that SHA> <chain branch>`. A non-zero exit means the worktree was cut from the default branch anyway: that chain is **not** merged, the loop stops, and `flow` tells you to restart the session and run it again to resume. The chain's worktree and branch stay on disk, so nothing it built is lost. Merging a chain off the wrong base would bury the mistake under a merge commit, where it stops looking like a mistake at all.

**Two chains never edit the same file.** That is a rule on the plan, not a hope about the merge. A piece that has to touch a file another chain owns goes in `chain: final`, which runs alone after every other chain has merged. A conflict is far cheaper to prevent while writing the plan than to resolve in a branch nobody was watching.

**`git merge-tree --write-tree` before every merge.** It answers *would this conflict* without touching the working tree, so a conflict is found before anything is half-merged. A non-zero exit stops the job and names the two chains and the files. `flow` never resolves one: a conflict means the one-file-one-chain rule was broken, and that is a fix to the plan, not a patch buried in a merge commit.

**The merge is local, and it is not a pull request merge.** `flow` merges each chain branch into your feature branch on your machine, with `git merge --no-ff`, so every chain leaves one merge commit naming it and the builders' own SHAs stay exactly as they reported them. The default branch is never touched. `submit` still opens the PR, `ship` is still the only thing that merges it, and only you can start `ship`.

**Four chains at once.** A cap, not a target. Four is the middle of the working range the field has settled on for parallel coding agents, and the ceiling is real: each builder is a full session with a checkout behind it, so a fifth costs more in rate limit and in reports you have to read than it buys in wall clock. Further chains wait for a slot.

**The builder runs on Sonnet.** That was your call, taken against this plugin's own "a cheaper model needs evidence first" line. Four builders at once multiplies the model choice by four, and the builder's job is the narrowest in the plugin: it is handed a written plan, one chain and a `Done when:` line, and `build`'s gates decide whether it was done. Effort stays `high`. It is recorded as a decision rather than a finding, so if plan quality drops this is the first thing to put back.

**If the harness cannot give a builder a worktree** — no `isolation` option, or the first spawn with it fails — `flow` says `chains in-session: no worktree isolation` once, then builds one chain at a time on your branch, spawning each builder without `isolation`, with no merge step and no cleanup. The builder's inputs and report do not change; its `branch:` line just names your branch. You lose the wall-clock time and nothing else.

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

## One feature per run

One flow run ends as one PR. A request that names three features would end as one PR carrying three things, or as a plan that mixes them, so `flow` splits before it sizes anything.

**Default is do not split.** A feature is something that could ship alone and that a user would ask for in its own sentence. Parts that depend on each other are one feature, not several — splitting those would hand `build` a piece that cannot pass on its own. And a request that already says how it wants to be built — "each as its own piece", "in one PR" — is one feature with pieces, not several features: the human shaped it, and its pieces belong to the plan, not the backlog.

The question comes before the size line, not after, because sizing needs to know which feature it is sizing. Ask first, size the one kept feature second, and the size line means what it says.

The rest are parked, never dropped. A project whose `## Plans` block says `github` gets one issue per parked feature, labelled `devflow:backlog` — `setup` makes that label alongside `devflow:plan`, and `flow` makes it too if a project set up before this existed. Everything else — no block, `local`, or `gh` failing on the day — writes one file per parked feature at `.devflow/backlog/<short-name>.md` instead.

A later run given `.devflow/backlog/<name>.md` as its request reads the file as the request and deletes it in the same branch, so the deletion ships with the PR that finally builds it. Nothing lingers to be parked twice.

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
