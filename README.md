# devflow

One dev loop for features, changes, bug fixes and chores.

It sizes the work. It writes the test first. It proves the code runs. Then it opens a PR. It ships only when you say so.

It asks you as little as possible.

This is **Phase 1**. It is small on purpose.

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

It also asks where Deep plans live. Local is the default: a file in `.devflow/plans/`. Pick `github` and each Deep plan becomes an issue, labelled `devflow:plan`, closed when the work merges. It writes a `## Plans` block only after `gh` has answered. Picking `github` also makes a second label, `devflow:backlog`, for the features `flow` parks rather than builds.

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

A request that names more than one feature keeps one and parks the rest — as a GitHub issue labelled `devflow:backlog`, or a file under `.devflow/backlog/` — so one run still ends as one PR and nothing named gets lost.

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
      ├── Standard, and a bug nobody        │                │
      │   can point at ──► debug ───────────┤                │
      │   finds the cause, proves it        │                │
      │   with one red command              │                │
      │                                     │                │
      ├── Standard ── unclear? ── no ───────┤                │
      │                  │                  │                │
      │                 yes                 │                │
      │                  │                  │                │
      └── Deep ──────────┴──► ask, once ────┤                │
                              [YOU] answer, │                │
                              or take the   │                │
                              recs. Plan    │                │
                              researches,   │                │
                              then writes it│                │
                                            ▼                │
                    ┌───────────────────► build              │
                    │                     write the test     │
                    │                     watch it fail      │
                    │                     make it pass       │
                    │                     Deep: plan runs    │
                    │                     one builder agent  │
                    │                     per chain, chains  │
                    │                     in parallel, each  │
                    │                     commits            │
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
                  failure?     ▲           the PR
                  then fix     │            │
                               └─ conflict only, from ship below
                                            ▼
                                [YOU] /devflow:ship
                                      merge. Watch the deploy.
                                      Check it is live. Tidy up.
```

A bug nobody can point at takes a short detour on the Standard branch, before `build`:
`devflow:debug` finds the cause and proves it with one red command, then hands that
command to `build` as its first failing test. A bug you can already point at skips the
detour and goes straight into the same `build` box.

There is a second view of the same thing in [docs/pipeline.md](docs/pipeline.md). It shows where work can *sit*, and what is allowed to move it. This chart answers what happens next. That one answers where the work is now.

The three `[YOU]` marks are the only places you are normally needed. The third, `ship`, is the one only you can start.

Here is what the chart leaves out. All of it stops the flow rather than bending it:

- `flow` forces anything on the **danger list** to at least Standard size. When it is one of the security items, `review` starts `security-reviewer` on its own, inside `submit`'s own review step — nothing for you to remember to run.
- The **hook asks** before any commit that would land on the default branch.
- **Three failed attempts** at the same problem and `build` stops. It says what each attempt ruled out. It does not try a fourth.
- If the **live check fails** twice, `submit` stops and does not open a PR. An honest failure beats a green-looking PR over a broken feature.
- A **builder that says `stuck`** stops a Deep job. `plan` stops spawning new chains, lets the running ones finish, then says which chain and which piece, and what the builder ruled out, before handing it to you. It does not try that piece again.

| Size | For | What happens |
|---|---|---|
| **Quick** | Typos, chores, most bug fixes | Straight to building. No questions. |
| **Standard** | Changing existing behaviour | Shows what it will do, then waits for your go. Questions only if genuinely unclear. |
| **Deep** | New features, wide refactors | Rounds of popup questions until no answer would change the plan. Then a written plan, checked against the summary you approved, and one builder agent per chain of pieces, several chains at once in their own worktrees. |

It announces the size in one line before doing anything. That way you can disagree straight away.

### Learning from runs

A second, slower loop sits beside the first. It turns mistakes in real runs into skill fixes.

```
flow         you overrode the size             ──┐
review       hardcase refuted a finding        ──┤
ship         Verify failed after the deploy    ──┤  one line each
[YOU]        /devflow:lesson "..."             ──┤
                                                 ▼
                            lessons.md, in the private
                            eddiechok/devflow-lessons repo
                                                 ┆  about once a month
                                                 ▼
                            [YOU] /devflow:lesson-review
                                  counts waste from saved sessions
                                  proposes a change only on a repeat,
                                  each with a new eval case, run
                                  old against new
                                                 │
                                                 ▼
                            [YOU] yes to one proposal
                                  applied as shown, then the
                                  frontmatter test and validate run
```

A fact about your project is not a devflow lesson. `submit` puts that in the project's own `CLAUDE.md`, in the same PR, so you approve it with the work. [docs/lessons.md](docs/lessons.md) has the rules.

### When it will ask you

**Direction.** Deep jobs always ask. Standard asks only when genuinely unclear. Quick never asks.

**Go.** Standard and Deep show what they will change as a short report — the size, a table of the changes and where each lands, what you will see, and any tracker actions — then wait for your go before the first edit. On Deep that comes with the questions. After the plan is written, Deep shows a report of its pieces and goes on; it asks for your go again only if the pieces drifted from what you approved. Quick shows the same report and carries on.

Questions come as popups, up to 4 a round, shown one at a time, each with 2 to 4 options and the recommended one first. Pick it, or pick Other and type your own. Rounds go on until no open question could change a todo line, a plan piece, or what the user sees, and there is no cap on them. Ask for an explanation and you get it in plain words, then the same question again. On Standard and Deep the todo block sits above the popup, and answering approves it. Where there is no popup tool, in evals and `claude -p`, it asks a numbered list instead, and `yes to all` is a valid reply there. Anything you skip takes the recommendation, and appears in the PR under **Assumptions**.

Two rules decide what gets into a round.

**Facts are the plugin's job. Decisions are yours.** If the repo already holds the answer, it reads the repo. It does not ask you. You would answer from memory. The code cannot be wrong about itself.

**It asks only what is answerable now.** A question that another question decides is held back, and asked in the next round if the answer that settles it opens it. A question no answer to which could change the build is not asked: it takes the recommendation.

**Merge.** Always yours. `submit` opens the PR and stops. `/devflow:ship` does everything after it.

`ship` is the one skill you have to start yourself. `disable-model-invocation: true` keeps it out of the automatic path. `flow` and `submit` are both told never to call it.

**Committing to the default branch.** The hook asks first.

That is it. A one-line bug fix asks you nothing until merge.

### The danger list

These always get at least Standard size and a human check. The first five also start `security-reviewer` automatically, inside `review`:

auth and permissions · secrets and keys · payments · public API or wire format · CI/CD config · database migrations · deleting or weakening tests · anything that cannot be reverted

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
| `flow` | Sizes the request. Routes it. Asks any questions in popup rounds |
| `debug` | A bug nobody can point at, before `build` sees it: builds a red-capable loop, ranks 3 to 5 falsifiable causes, and hands the confirmed one to `build` as its first failing test. Called by `flow`, or start it by hand |
| `plan` | Deep work only: writes the plan, revises it, resumes it, and runs one builder per chain. Called by `flow`, or start it by hand — it writes or revises the plan and stops, then tells you `/devflow:flow` builds it |
| `build` | Test first. Watch it fail for the right reason. Then make it pass |
| `review` | Ranked axes in fresh agents: is it built right, is it safe from an attacker, is it the right thing. Reported side by side, never blended. The security axis runs only when the danger list calls for it. When `build` found no behaviour to test, only the built-right axis runs, to check the words still match the repo |
| `submit` | Runs the checks fresh. Runs the app. Calls `review`. Commits. Opens the PR, or updates the one already open. **Never merges** |
| `tend` | After the PR is open. Works out what a red check or a review comment is really saying. Checks whether this branch caused it. Then fixes it and re-submits |
| `ship` | Merges it. Watches the deploy. Checks it is really live. Cleans up. **Only you can start it** |
| `lesson` | Writes one line to the private lessons repo — a mistake, an idea, or an override — so a later review can spot a pattern |
| `lesson-review` | Reads the lessons and counts waste from saved sessions. Proposes a skill change only on a repeat, each with an eval case. **A human approves every change**. You start it yourself |

`submit` opens the PR. `ship` merges it. Only you can start `ship`. On a branch with no PR, `ship` stops and points you at `submit`. Where a PR exists, it merges.

`review` runs agents that never saw the session: `reviewer` asks *is it built right*, `security-reviewer` asks *is it safe from an attacker* — only when the danger list names a security item — and `spec-reviewer` asks *is it the right thing*. Another, `hardcase`, tries to break `reviewer`'s and `security-reviewer`'s findings. The reports are never blended. `researcher` is not a reviewer either: on a Deep job, `flow` and `plan` start one per open question, at most 3 each, `flow` during its rounds and `plan` before it writes the pieces, and each finding it returns names its source. `builder` is not a reviewer: on a Deep job it builds one chain of the plan's pieces in its own git worktree, commits each one, and reports back a branch line plus five lines per piece. One builder per chain, up to four chains at once, and `plan` merges their branches back before it reports to `flow`, which then submits.

Folder copies get cleaned up behind the work. The worktrees `plan` cuts for a Deep job's chains are removed when they merge. The one `flow` step 0c or `tend` takes for the session itself holds your branch, so it stays until `ship` merges that branch. `ship` then removes it only when it holds nothing: no uncommitted files, no commits of its own. Otherwise it stays, and `ship`'s `cleaned` line says so. If `ship` never runs, the harness asks you to keep or remove it when the session ends.

## More

One page each. Read them when you need them. A skill holds its steps; the page named
after it holds why those steps are what they are, and you only need it if a rule looks
wrong.

| Page | What it covers |
|---|---|
| [docs/flow.md](docs/flow.md) | Why `flow`'s steps are what they are. Follow-ups on an open PR. One feature per run, parking the rest to `devflow:backlog` or `.devflow/backlog/`. Why new work in a folder parked on someone else's branch takes a worktree of its own. The `CONTEXT.md` glossary. Size overrides. |
| [docs/debug.md](docs/debug.md) | Why `debug`'s phases are what they are. Why it never writes a fix. Why the loop comes before everything else. Why the ranked list of causes is shown, not waited on. |
| [docs/plan.md](docs/plan.md) | Why `plan`'s steps are what they are. Where a Deep plan goes and how revising one works. One builder per chain, in parallel worktrees. Plans kept as GitHub issues. Starting `plan` by hand. |
| [docs/build.md](docs/build.md) | Why `build`'s gates are what they are. Running the checks bare. Where the expected value comes from. Watching it fail. When there is nothing a test could catch. |
| [docs/submit.md](docs/submit.md) | Why `submit`'s steps are what they are. Checks that postdate the last edit. The live check. The commit and the PR body. |
| [docs/review.md](docs/review.md) | Why `review`'s steps are what they are. The four agents. Why the axes are separate and ranked apart. Why `hardcase` defaults to *falls*. Why a change with no behaviour gets one reader. |
| [docs/ship.md](docs/ship.md) | Why `ship`'s steps are what they are. The boundary only a human crosses. Choosing a method the branch can take. The three real merge-error runs. The deploy block. |
| [docs/tend.md](docs/tend.md) | Why `tend`'s steps are what they are. Getting on the PR's branch first. Triage before anything is changed. |
| [docs/setup.md](docs/setup.md) | Why `setup`'s steps are what they are. Everything downstream trusts the `## Checks` block. Running each command before writing it down. |
| [docs/pipeline.md](docs/pipeline.md) | Where work can sit, and what moves it. |
| [docs/lessons.md](docs/lessons.md) | How `lesson` and `lesson-review` capture and act on real runs. Where waste counting reads from, and what it cannot see. The loop that turns a repeat into a fix and an eval case. |
| [docs/web.md](docs/web.md) | Claude Code on the web. Start with "use the devflow flow skill". On Pro, say "run the review". `ship` is local only. |
| [docs/hook.md](docs/hook.md) | The bash hook. It trims check output, allows the bare check commands, and asks before a commit to the default branch. It stops mistakes, not attackers. |
| [docs/provenance.md](docs/provenance.md) | Where every idea came from. Every bug that shaped a rule. Full credits. |

Working on the plugin? The checks are in [CLAUDE.md](CLAUDE.md). `claude plugin validate .` prints exactly one warning, about `version`. That is on purpose.

## Borrowed from

[obra/superpowers](https://github.com/obra/superpowers), [mattpocock/skills](https://github.com/mattpocock/skills), [wshobson/commands](https://github.com/wshobson/commands), [heliohq/ship](https://github.com/heliohq/ship), and Anthropic's [code-review](https://github.com/anthropics/claude-plugins-official) plugin. Which idea came from where is in [docs/provenance.md](docs/provenance.md#credits-in-full).

## License

MIT. See [LICENSE](LICENSE).
