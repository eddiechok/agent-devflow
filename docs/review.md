# review, and its three agents

`review` does not review. It pins the range. It finds the spec. Then it spawns these two, which have never seen the session that wrote the code:

| Agent | Axis | What it does |
|---|---|---|
| `reviewer` | Is it built right | Reads the whole branch, committed and not. Reports only findings it can attach a concrete failing case to |
| `spec-reviewer` | Is it the right thing | Reads the plan, the issue, or the request the human typed, which `flow` passes down. Reports what is missing, what was built wrong, and what nobody asked for. Runs only when one of those was found |
| `hardcase` | Is the first axis right | Gets `reviewer`'s findings and tries to **break** them. Reports which stand, which fall and why. Runs only when `reviewer` found something |

`review` prints the two axis reports side by side. It **never merges them, and never ranks one against the other**.

A change can follow every rule in the repo while building the wrong thing. A blended verdict lets the passing axis hide the failing one.

`hardcase` is not a third axis. It sits under **Built right**, because that is the axis it argues with. It never appears in the summary, because there is no worst challenge.

It exists because the two axes are not symmetrical. Every `spec-reviewer` finding quotes the line of the spec it rests on. So it is already anchored outside the reviewer's own judgement.

`reviewer`'s bar is different. It has to name a failing case. But a plausible case that cannot actually be reached still clears that bar. So the expensive false positive is always on the first axis. That is the one `hardcase` argues with.

`hardcase` defaults to **falls**. A finding it cannot confirm from the code does not survive. That asymmetry is the point. It is what makes a `Stands` worth acting on.

But `hardcase` gets no vote. A finding that fell is still printed, with the reason. `submit` checks the refuting line itself before dropping anything. Two agents disagreeing is not a majority. It is one of them having read something the other did not.

All three are agents, not prompt templates. `tools:` grants read, grep, glob and bash. None has Edit or Write, and none can start another agent. Those two limits are real. But bash can still write a file or run `git`. So "never edit" is a rule in each prompt, not a wall in the harness. Bash stays because `git diff` is how they read the change.

All three pin `model: opus` and `effort: xhigh`. A review does not quietly become a cheaper review because of what you happened to have `/model` set to. An under-powered review still prints, and still reports nothing wrong.

The two axes pin the **same** pair on purpose. Their reports are never ranked against each other. A weaker model on one axis would rank them without saying so.

`hardcase` pins it for a different reason. A refuter that cannot follow the code refutes nothing. It prints a clean sheet that reads like agreement.

## The one change that gets no review

`submit` can hand `review` a line `no-behaviour: <reason>`. Then no agent starts at all, and all three sections of the report read `skipped — no behaviour`.

The reason comes from `build`, which has a gate for the change that no test can catch. Carrying that answer forward is cheaper than paying three Opus agents to rediscover it, and it is the only place in the plugin where a review is skipped outright rather than merely finding nothing.

It is a **third state**. `NOT RUN` is an axis that should have run and could not — a finding for the PR. `none` is an axis that ran and found nothing. `skipped — no behaviour` is an axis that was never owed a run, and `submit` reads it as nothing to fix.

`review` never works it out for itself. It cannot: deciding would mean reading the change in order to judge whether the change is worth reading. Nor can file types stand in — in this repo a `.md` skill file is the behaviour, so a rule keyed on the extension would skip the review on exactly the changes that most need one.

## The reasons, step by step

Every paragraph below was moved here out of `skills/review/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

### Step 1 — pinning the fixed point

A typo'd ref or an empty range fails here, in front of the human, rather than inside two
agents that then review nothing and report nothing wrong.

### Step 2 — finding the spec

Do not match the filename against the branch name: a harness that names your branch for
you, as Claude Code on the web does, makes that match fail on exactly the work that has a
spec.

A spec you could not read is not a spec, but the request may still be one.

Standard work has no plan file, so the words the human typed are the only spec there is.

A request you were not handed is not a spec: after a `/clear` it is gone, and the answer
is the one below, as it always was.

That is a normal answer for a Quick fix, or for a `review` you started yourself on a
branch.

### Step 3 — spawning the axes

Fresh context is the whole point.

#### Then challenge the first axis

This is the one place in the plugin where the expensive step is skipped by default, and it
is safe because it is skipped exactly when there is no work for it.

`spec-reviewer`'s findings each quote the line of the spec they rest on, so they are
already anchored to something outside the reviewer's judgement. `reviewer`'s are not — its
bar is naming a failing case, and a plausible case that cannot actually be reached passes
that bar. That is the gap `hardcase` closes.

A challenge is one more thing on the table, not a verdict that removes one.

#### When the harness will not let you spawn an agent

**This is a plan restriction, not a web one** — it rides on Pro, and it fires locally
exactly as it does on the web, so do not go looking for it by asking where you are
running.

Getting this backwards costs in both directions. Assume it is a web rule and a Pro session
working locally hits the block with no warning and no `NOT RUN` line. Assume every web
session has it and a Max or Team session on the web stops to ask a question nothing was
blocking, then labels a review `NOT RUN` that would have run.

An axis that did not run is not a clean axis.

### Step 4 — reporting both

Both readings go to `submit` together; the point is that whoever decides can see the
argument, not just its outcome.

A change can follow every rule in the repo while building the wrong thing, or build
exactly the right thing in a way the repo forbids. One blended verdict lets the passing
axis hide the failing one, which is the whole reason the axes are separate.

An axis that ran out of room is not an axis that found nothing, and `submit` decides what
to fix from what you print.

Where every step came from is in [docs/provenance.md](docs/provenance.md).
