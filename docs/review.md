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

Where every step came from is in [docs/provenance.md](docs/provenance.md).
