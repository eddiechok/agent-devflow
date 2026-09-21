# devflow

One dev loop for features, changes, bug fixes and chores.

It sizes the work. It writes the test first. It proves the code runs. Then it opens a PR. It ships only when you say so.

It asks you as little as possible.

This is **Phase 1**. It is small on purpose. See [What is not here yet](#what-is-not-here-yet).

## The three rules

They are in order. When two disagree, the higher one wins.

**1. Be correct, and prove it.** If the work is wrong, nothing else matters. A claim with no proof counts as wrong until shown otherwise. "Tests pass" needs the output. "Reviewed" needs the report. "Live" needs the page.

**2. Ask as little as possible, but not less than that.** Zero questions is not the goal. The goal is few interruptions, placed where they matter most.

**3. Spend where it matters.** A typo gets no questions and no plan. A review gets the best model, every time. Never save on code review, hard bugs, or anything on the danger list.

## Install

```bash
/plugin marketplace add eddiechok/agent-devflow
/plugin install devflow@eddiechok-devflow
```

Or install it everywhere at once. Add this to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "eddiechok-devflow": {
      "source": { "source": "github", "repo": "eddiechok/agent-devflow" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "devflow@eddiechok-devflow": true }
}
```

## Set up a project

Run this once in each project:

```
/devflow:setup
```

It finds the test, typecheck and lint commands. It **runs them to prove they work**. Then it writes a `## Checks` block into the project's `CLAUDE.md`:

```markdown
## Checks
- Test: pnpm test
- Typecheck: pnpm typecheck
- Lint: pnpm lint
```

This block is the only thing a project must provide. The plugin hardcodes nothing. A wrong command here fails silently, so nothing gets written until it has run.

A line may repeat. Two `Test:` lines run in order. This repo's own [CLAUDE.md](CLAUDE.md) does that.

A second block, `## Deploy`, is optional. You never write it by hand. `ship` offers to add it after its first verified deploy.

It also asks where Deep plans live. Local is the default: a file in `.devflow/plans/`. Pick `github` and each Deep plan becomes an issue, labelled `devflow:plan`, closed when the work merges. It writes a `## Plans` block only after `gh` has answered.

Run it again if the commands change. It will not overwrite a block you wrote without asking.

## Use it

```
/devflow:flow add a settings page for email alerts
/devflow:flow #123
/devflow:flow --deep change how sessions are stored
```

Then, once you have looked at the PR and want it finished:

```
/devflow:ship
/devflow:ship 123
```

`flow` sizes the work and routes it. You should not normally need to call the others directly.

There are two exceptions. `ship` is the one skill nothing else can call. `flow` does route to `tend`. But you will usually start `tend` yourself, when you see a red check.

### The loop

```
/devflow:setup      once per project. Writes the Checks block.
      ┆
      ▼
/devflow:flow ◄──────────────────────────────────────────────┐
      │  size it. Say it in one line.                        │
      │                                                      │
      ├── Quick ────────────────────────────┐                │
      │                                     │                │
      ├── Standard ── unclear? ── no ───────┤                │
      │                  │                  │                │
      │                 yes                 │                │
      │                  │                  │                │
      └── Deep ──────────┴──► ask, once ────┤                │
                              [YOU] answer, │                │
                              or take the   │                │
                              recs. Deep:   │                │
                              plan written  │                │
                                            ▼                │
                    ┌───────────────────► build              │
                    │                     write the test     │
                    │                     watch it fail      │
                    │                     make it pass       │
                    │                     Deep: one builder  │
                    │                     agent per piece,   │
                    │                     each commits       │
                    │                       │                │
                    │                       ▼                │
                    │                     submit             │
                    │                     checks, fresh      │
                    │                     run the app        │
                    │                     review             │
                    │                     fix stale docs     │
                    │                     commit, push       │
                    │                     open the PR        │
                    │                       │                │
                    │                       ▼                │
                  tend ◄── red check ──── [YOU] ── changes ──┘
                  whose    or comments     review
                  failure?                 the PR
                  then fix                  │
                                            ▼
                                [YOU] /devflow:ship
                                      merge. Watch the deploy.
                                      Check it is live. Tidy up.
```

There is a second view of the same thing in [docs/pipeline.md](docs/pipeline.md). It shows where work can *sit*, and what is allowed to move it. This chart answers what happens next. That one answers where the work is now.

The three `[YOU]` marks are the only places you are normally needed. The third, `ship`, is the one only you can start.

Here is what the chart leaves out. All of it stops the flow rather than bending it:

- `flow` forces anything on the **danger list** to at least Standard size. `submit` also names `/security-review` in its handoff. That one is a slash command, so only you can start it.
- The **hook asks** before any commit that would land on the default branch.
- **Three failed attempts** at the same problem and `build` stops. It says what each attempt ruled out. It does not try a fourth.
- If the **live check fails** twice, `submit` stops and does not open a PR. An honest failure beats a green-looking PR over a broken feature.
- A **builder that says `stuck`** stops a Deep job. `flow` says which piece, and what the builder ruled out, then hands it to you. It does not try that piece again.

| Size | For | What happens |
|---|---|---|
| **Quick** | Typos, chores, most bug fixes | Straight to building. No questions. |
| **Standard** | Changing existing behaviour | Questions only if genuinely unclear. |
| **Deep** | New features, wide refactors | One round of questions, two at most. Then a written plan, and one builder agent per piece. |

It announces the size in one line before doing anything. That way you can disagree straight away.

### When it will ask you

**Direction.** Deep jobs always ask. Standard asks only when genuinely unclear. Quick never asks.

All questions come at once, each with a recommended answer. `yes to all` is a valid reply. Anything you skip takes the recommendation, and appears in the PR under **Assumptions**.

Two rules decide what gets into that round.

**Facts are the plugin's job. Decisions are yours.** If the repo already holds the answer, it reads the repo. It does not ask you. You would answer from memory. The code cannot be wrong about itself.

**It asks only what is answerable now.** A question that another question decides is held back. Held questions take the recommendation. Deep may ask one more round, for a held question the plan needs. Two is the ceiling.

**Merge.** Always yours. `submit` opens the PR and stops. `/devflow:ship` does everything after it.

`ship` is the one skill you have to start yourself. `disable-model-invocation: true` keeps it out of the automatic path. `flow` and `submit` are both told never to call it.

**Committing to the default branch.** The hook asks first.

That is it. A one-line bug fix asks you nothing until merge.

### The danger list

These always get at least Standard size, a human check, and a security review:

login and permissions · secrets and keys · payments · database migrations · public APIs · CI/CD config · deleting or weakening tests · anything that cannot be reverted

### Escape hatches

| You want | Do this |
|---|---|
| See the full output of a check | add `--verbose` to the command |
| Skip the commit guard | append `# devflow-ok` to the command |
| Force a bigger or smaller process | `/devflow:flow --deep` or `--quick` |

## The skills

| Skill | What it does |
|---|---|
| `setup` | Once per project. Finds and verifies the check commands. You invoke it yourself, so it costs nothing at runtime |
| `flow` | Sizes the request. Routes it. Asks any questions in one batch |
| `build` | Test first. Watch it fail for the right reason. Then make it pass |
| `review` | Two axes in fresh agents: is it built right, is it the right thing. Reported side by side, never blended |
| `submit` | Runs the checks fresh. Runs the app. Calls `review`. Commits. Opens the PR, or updates the one already open. **Never merges** |
| `tend` | After the PR is open. Works out what a red check or a review comment is really saying. Checks whether this branch caused it. Then fixes it and re-submits |
| `ship` | Merges it. Watches the deploy. Checks it is really live. Cleans up. **Only you can start it** |

`submit` opens the PR. `ship` merges it. Only you can start `ship`. On a branch with no PR, `ship` stops and points you at `submit`. Where a PR exists, it merges.

`review` runs two agents that never saw the session: `reviewer` asks *is it built right*, `spec-reviewer` asks *is it the right thing*. A third, `hardcase`, tries to break `reviewer`'s findings. The two reports are never blended. A fourth, `builder`, is not a reviewer: on a Deep job it builds one plan piece, commits it, and reports back in five lines. One builder per piece.

## More

One page each. Read them when you need them.

| Page | What it covers |
|---|---|
| [docs/flow.md](docs/flow.md) | Follow-ups on an open PR. Where a Deep plan goes. One builder per piece. The `CONTEXT.md` glossary. Size overrides. |
| [docs/review.md](docs/review.md) | The three agents. Why two axes. Why `hardcase` defaults to *falls*. |
| [docs/pipeline.md](docs/pipeline.md) | Where work can sit, and what moves it. |
| [docs/web.md](docs/web.md) | Claude Code on the web. Start with "use the devflow flow skill". On Pro, say "run the review". `ship` is local only. |
| [docs/hook.md](docs/hook.md) | The bash hook. It trims check output, allows the bare check commands, and asks before a commit to the default branch. It stops mistakes, not attackers. |
| [docs/provenance.md](docs/provenance.md) | Where every idea came from. Every bug that shaped a rule. Full credits. |

Working on the plugin? The checks are in [CLAUDE.md](CLAUDE.md). `claude plugin validate .` prints exactly one warning, about `version`. That is on purpose.

## What is not here yet

Phase 1 is the smallest useful thing. These stay out on purpose:

- A standalone `plan` skill. You cannot revise a plan once written.
- `debug`, a bug-fixing loop. Bugs go through `build` for now.
- Model routing by size. A skill cannot change its own model.
- Cleanup of worktrees and folder copies.
- Capturing lessons.

Add each one when two weeks of real use shows you need it. Not before.

## Borrowed from

[obra/superpowers](https://github.com/obra/superpowers), [mattpocock/skills](https://github.com/mattpocock/skills), [wshobson/commands](https://github.com/wshobson/commands), [heliohq/ship](https://github.com/heliohq/ship), and Anthropic's [code-review](https://github.com/anthropics/claude-plugins-official) plugin. Which idea came from where is in [docs/provenance.md](docs/provenance.md#credits-in-full).

## License

MIT. See [LICENSE](LICENSE).
