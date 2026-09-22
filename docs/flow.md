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

## One builder per piece

The session that wrote the plan does not build it. Each piece goes to a fresh `builder` agent, one at a time, in plan order.

The reason is the window. One session building every piece is full of piece 1 by the time piece 4 starts. Then compaction keeps a summary and drops the plan. With a builder per piece, the session holds the plan and five lines per piece: `piece`, `test`, `commit`, `seam`, `stuck`.

The builder gets three things: the plan path, the piece number, and whether the tree is dirty. It runs the `build` skill on that piece, commits it, and reports. It cannot ask you anything. So each piece carries a `Done when:` line, which is where it stops. If a seam was unclear, it says which one it picked. If it fails three times, or hits a design decision the plan did not make, it says `stuck`, and `flow` stops the job and hands it to you. If a piece is done but the builder has a doubt, it says so, and the doubt lands in the PR under Assumptions.

Never two builders at once. Two agents committing to one branch is a merge conflict with nobody to solve it.

On a harness that only starts agents when you ask, `flow` asks once for the whole job. Say no, and it builds every piece in the session, as it did before. Nothing is lost but the window.

Quick and Standard do not change. One piece, one session.

Commit the file or ignore it, as you prefer. devflow does not add it to `.gitignore`. It does not expect it there either.

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

### Step 4 — one builder per piece

One session building every piece fills its own window with piece 1 by the time piece 4
starts, and then compaction keeps a summary and drops the plan.

The plan holds everything a piece needs, and that is the test of whether the plan is good.

Printing it is not what keeps it: the builder also wrote it as a `Concern:` line in the
piece's commit body, which is what `submit` reads into the PR's **Assumptions** after any
`/clear`.

Two builders committing to one branch at once is a merge conflict nobody is there to solve,
and a piece that depends on the one before it cannot start until that one is in. Sequential
is the whole design; parallel builders in worktrees are a later change, if sequential ever
proves too slow.

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
