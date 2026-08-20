# devflow

One dev loop for features, changes, bug fixes and chores.

It sizes the work. It writes the test first. It proves the code runs. Then it opens a PR. It ships only when you say so.

It asks you as little as possible.

This is **Phase 1**. It is small on purpose. See [What is not here yet](#what-is-not-here-yet).

## The three rules

They are in order. When two disagree, the higher one wins.

**1. Be correct, above everything else.** If the work is wrong, nothing else matters. Sometimes being cheap makes you redo the work. That is not a cost decision. That is a correctness problem in disguise.

**2. Ask as little as possible, but not less than that.** Zero questions is not the goal. The goal is few interruptions, placed where they matter most.

**3. Be cheap where it is a real trade.** Never be cheap on code review. Never on hard bugs. Never on anything on the danger list.

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

It finds the project's test, typecheck and lint commands. It **runs them to confirm they work**. Then it writes a `## Checks` block into the project's `CLAUDE.md`:

```markdown
## Checks
- Test: pnpm test
- Typecheck: pnpm typecheck
- Lint: pnpm lint
```

This block is the **only** thing each project must provide. It is what makes devflow work with any language.

No commands are hardcoded in the plugin. The project is the source of truth.

Any line may repeat. Say a project has two test commands and no wrapper that runs both. It gets two `Test:` lines, run in order. Two honest lines beat one invented wrapper script. This repo's own [CLAUDE.md](CLAUDE.md) is an example.

There is a second block called `## Deploy`. It is optional, and you never write it by hand.

`ship` offers to add it the first time it deploys and verifies successfully. That is the only moment anything has proof the command works.

`setup` leaves it alone on purpose. Its rule is that it runs a command before recording it. The only way to check a deploy command is to deploy.

Run `/devflow:setup` again if the commands change. It will not overwrite a block you wrote yourself without asking.

Why does it run the commands instead of just writing them down? Everything downstream trusts this block. A wrong command here fails silently. `submit` runs something harmless, sees exit 0, and reports the work as proven.

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

There are two exceptions. `ship` is the one skill nothing else can call. And `tend` is one that `flow` does route to, but you will usually reach for it yourself, the moment you see a red check.

### The loop

```mermaid
flowchart TD
    SETUP(["/devflow:setup, once per project"]) -.->|"writes the Checks block"| REQ
    REQ(["/devflow:flow what you want"]) --> SIZE{"Size it, announce it<br/>in one line"}

    SIZE -->|Quick| BUILD
    SIZE -->|Standard| CLEAR{"Genuinely<br/>unclear?"}
    SIZE -->|Deep| ASK
    CLEAR -->|no| BUILD
    CLEAR -->|yes| ASK

    ASK["One batch of questions,<br/>each with a recommendation"] --> YOU1{{"You answer, or skip and<br/>take the recommendations"}}
    YOU1 -->|"Deep: plan saved to .devflow/plans/"| BUILD

    BUILD["build<br/>write the test<br/>watch it fail<br/>then make it pass"] --> SUBMIT["submit<br/>feature branch<br/>checks re-run fresh<br/>run the app, code review<br/>conventional commit, push"]
    SUBMIT --> YOU2{{"You review the PR"}}
    YOU2 -->|"want changes"| REQ
    REQ -->|"PR already reporting something"| TEND
    YOU2 -->|"CI red, or comments"| TEND["tend<br/>triage what the PR reports<br/>whose failure is it<br/>then fix it"]
    TEND --> BUILD
    YOU2 -->|"/devflow:ship"| SHIP["ship<br/>merge<br/>watch the deploy<br/>check it is really live<br/>delete the branch, tidy up"]

    classDef human fill:#fde68a,stroke:#b45309,color:#111
    class YOU1,YOU2 human
```

There is a second view of the same thing in [docs/pipeline.md](docs/pipeline.md). It shows where work can *sit*, and what is allowed to move it. This chart answers what happens next. That one answers where the work is now.

The two amber boxes are the only places you are normally needed.

Here is what the chart leaves out. All of it stops the flow rather than bending it:

- Anything on the **danger list** is forced to at least Standard size. `submit` also names `/security-review` in its handoff. That one is a slash command, so only you can start it.
- The **hook asks** before any commit that would land on the default branch.
- **Three failed attempts** at the same problem and `build` stops. It says what each attempt ruled out. It does not try a fourth.
- If the **live check fails** twice, `submit` stops and does not open a PR. An honest failure beats a green-looking PR over a broken feature.

| Size | For | What happens |
|---|---|---|
| **Quick** | Typos, chores, most bug fixes | Straight to building. No questions. |
| **Standard** | Changing existing behaviour | Questions only if genuinely unclear. |
| **Deep** | New features, wide refactors | One round of questions, then a written plan. |

It announces the size in one line before doing anything. That way you can disagree straight away.

### Changing the PR after you have looked at it

`submit` stops at the pull request. You read it and want something different. Go back through `flow`.

`flow` checks the branch first. It sees the open PR. It treats the request as a **follow-up**. Same branch, same PR. `submit` **updates** it instead of opening a second one.

Follow-up mode reads before it asks. The PR's **Assumptions** and the plan file already hold what you decided the first time. So you are only asked what is genuinely new.

Sizing still runs. A follow-up can be anything from a typo to a rethink. The danger list still applies.

Maybe the thing you want changed is something the **PR itself is reporting**. A check went red. A reviewer asked for something. Then `flow` hands it to `tend` instead of taking it into `build`.

Not every failure a pull request reports belongs to that pull request. `tend` is the step that asks whose it is, before anything gets pushed.

The request may turn out to be new work rather than a change to that PR. Then `flow` says so and starts a fresh branch. Where the branch is pinned and it cannot, it asks you which you meant.

### Where a Deep plan goes

Deep work writes its plan into the project, at `.devflow/plans/<short-name>.md`. The plan holds the assumptions taken. It also holds the pieces to build. Each piece is marked as depending on another piece or not.

That file is the spec, not a progress tracker. Its job is to hold the assumptions and the pieces. It is also what `review`'s second axis judges the work against.

**A plan is resumable. The record is `git log`, not the file.** `build` commits each piece as it goes green. So you can `/clear` between pieces and pick up from the plan plus the log. The plan says what the pieces are. The log says which of them exist.

Nothing has to remember to tick a box. That is the reason to trust it. It is also why the checkbox version of this was rejected.

Commit the file or ignore it, as you prefer. devflow does not add it to `.gitignore`. It does not expect it there either.

### If it sizes something wrong

```
/devflow:flow --deep <request>
/devflow:flow --quick <request>
```

Overrides are recorded to `~/.claude/devflow/overrides.md`. They go there **globally, not per project**. They are notes about this plugin, not about any one repo. They are only useful when reviewed together.

`flow` also prints the line it wrote.

⚠️ On a hosted session that home directory sits inside a container. The container is deleted when the session ends. The file does not survive, so the reply is the only copy. Paste it somewhere durable if you work on the web.

Each line is a real example of the classifier getting it wrong, with your correction. After a month you have a set of labelled cases from actual use. That beats any examples invented up front. Do not delete the file.

This is the only self-improvement machinery in Phase 1. It only collects, on purpose. There is no review step yet.

Read the file when it has twenty or so lines in it. See whether a pattern is there. If one is, that is a change to `flow`. Make it through the normal flow, since this repo is just another project.

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

## The agents

`review` does not review. It pins the range. It finds the spec. Then it spawns these two, which have never seen the session that wrote the code:

| Agent | Axis | What it does |
|---|---|---|
| `reviewer` | Is it built right | Reads the whole branch, committed and not. Reports only findings it can attach a concrete failing case to |
| `spec-reviewer` | Is it the right thing | Reads the plan or issue. Reports what is missing, what was built wrong, and what nobody asked for. Runs only when a spec exists |
| `hardcase` | Is the first axis right | Gets `reviewer`'s findings and tries to **break** them. Reports which stand, which fall and why. Runs only when `reviewer` found something |

The two axis reports are printed side by side. They are **never merged or ranked against each other**.

A change can follow every rule in the repo while building the wrong thing. A blended verdict lets the passing axis hide the failing one.

`hardcase` is not a third axis. It sits under **Built right**, because that is the axis it argues with. It never appears in the summary, because there is no worst challenge.

It exists because the two axes are not symmetrical. Every `spec-reviewer` finding quotes the line of the spec it rests on. So it is already anchored outside the reviewer's own judgement.

`reviewer`'s bar is different. It has to name a failing case. But a plausible case that cannot actually be reached still clears that bar. So the expensive false positive is always on the first axis. That is the one that gets argued with.

`hardcase` defaults to **falls**. A finding it cannot confirm from the code does not survive. That asymmetry is the point. It is what makes a `Stands` worth acting on.

But `hardcase` gets no vote. A finding that fell is still printed, with the reason. `submit` checks the refuting line itself before dropping anything. Two agents disagreeing is not a majority. It is one of them having read something the other did not.

All three are agents rather than prompt templates. So their limits are real rather than requested. `tools:` grants read, grep, glob and bash. None of them can edit a file or start another agent.

All three pin `model: opus` and `effort: xhigh`. A review does not quietly become a cheaper review because of what you happened to have `/model` set to. An under-powered review still prints, and still reports nothing wrong.

The two axes pin the **same** pair on purpose. Their reports are never ranked against each other. A weaker model on one axis would rank them without saying so.

`hardcase` pins it for a different reason. A refuter that cannot follow the code refutes nothing. It prints a clean sheet that reads like agreement.

Where every step came from is in [docs/provenance.md](docs/provenance.md).

### Why `submit` does not run `/code-review`

It used to say it did. It could not, for three separate reasons. The failure was silent in the worst way. The instruction sat in the skill, looking like a review had happened.

- The plugin **may not be installed**. `submit` asserted it was.
- `/code-review` is a **slash command**. A skill cannot type one at itself, so nothing on the automatic path can start it.
- It reviews an **open pull request** and comments back on it. `submit` called for it at step 5, four steps before a PR exists.

So the work split by what can actually run where.

`review` is a skill, and its two axes are agents. A skill *can* start all three. They read a working tree. That is step 5.

`/code-review` gets handed to you at step 8, with the PR number. By then there is a PR for it to read. Neither one pretends to be the other.

### `ship` changed meaning. Read this once

`ship` used to mean *open a pull request and stop*. That job is now **`submit`**. `ship` is now the skill that merges and deploys.

The word moved onto a more dangerous action. So the old habit is worth breaking on purpose.

- Type `/devflow:ship` on a branch with **no PR**. It stops and points you at `submit`. The habit is caught.
- ⚠️ Type it where a **PR already exists**. It merges. Nothing catches that one.

## When it will ask you

**Direction.** Deep jobs always ask. Standard asks only when genuinely unclear. Quick never asks.

All questions come at once, each with a recommended answer. `yes to all` is a valid reply. Anything you skip takes the recommendation, and appears in the PR under **Assumptions**.

**Merge.** Always yours. `submit` opens the PR and stops. `/devflow:ship` does everything after it.

`ship` is the one skill you have to start yourself. `disable-model-invocation: true` keeps it out of the automatic path. `flow` and `submit` are both told never to call it.

**Committing to the default branch.** The hook asks first.

That is it. A one-line bug fix asks you nothing until merge.

## The danger list

These always get at least Standard size, a human check, and a security review:

login and permissions · secrets and keys · payments · database migrations · public APIs · CI/CD config · deleting or weakening tests · anything that cannot be reverted

## Escape hatches

| You want | Do this |
|---|---|
| See the full output of a check | add `--verbose` to the command |
| Skip the commit guard | append `# devflow-ok` to the command |
| Force a bigger or smaller process | `/devflow:flow --deep` or `--quick` |

## On Claude Code on the web

The plugin installs and loads the same way there. Put the `extraKnownMarketplaces` and
`enabledPlugins` block in the repo's own `.claude/settings.json`. Then it comes with the
clone.

But the web harness writes instructions of its own into the system prompt. Three of them
sit on top of devflow's steps.

**You have to start it yourself, and say it in words.** This is the one the plugin cannot
fix.

A web session opens with a task description. That description tells it to make the change,
commit and push. It is a complete loop, already given, before any skill is consulted. A
skill description does not outrank it.

Left alone, the session does the work well and does none of devflow. In the run that
prompted this section it invoked zero skills. It ran no review. It never opened the site.
It opened no PR.

Ask for it as **"use the devflow flow skill"** rather than `/devflow:flow`. A plugin's
skills do not always register as slash commands on the web. The Skill tool works either
way.

The durable version is a prefilled task link: `claude.ai/code?prompt=...&repositories=owner/repo`.
It puts the words in the box for you.

**The review may have to be asked for. But that is your plan, not the web.**

The instruction not to start an agent unless the human asked rides on **Pro**. It fires
locally exactly as it does on the web.

Both review axes are agents. Where that instruction applies, `review` says so in one line
and asks. Say **"run the review"** and both start.

If nothing is said, the axes report `NOT RUN`. `submit` carries that into the PR under
**Known issues**. A blocked review is never a clean one.

On Max or Team, nothing blocks it. That holds on the web and off. The question should
never appear.

**The PR is already asked for.** The harness says not to open a pull request unless the
human explicitly asked. Invoking `submit` *is* that request. So is `flow`, which ends in
it. `submit` says so rather than stopping to ask twice.

**Your branch is already made.** The harness creates it, and forbids pushing anywhere
else. So `build` keeps it instead of making a `<type>/<short-name>` one. Off the default
branch was always the real requirement. The naming was never the point.

**Deleting the merged branch may be refused.** Pushing a ref works. Deleting one answers
`403`. `ship` reports it and hands the branch to you rather than retrying. The merge is
untouched either way. The two are separate calls, which this skill already knew.

**`gh` is not pre-installed.** The web sandbox reaches GitHub through built-in tools and a
credential proxy. Those cover issues, pull requests, diffs and comments with no setup. So
every `gh` command in these skills names *what to ask for*, not *how to ask*.

You can also run `apt install -y gh` in the environment's setup script. It comes up
already authenticated through the same proxy.

⚠️ One catch either way. The proxy serves only a pinned set of GraphQL operations. So
`--json mergeStateStatus,statusCheckRollup,reviewDecision` can come back 403 where the
REST form works.

`ship` used to report a missing CLI as `none for this branch`. Those are the same words it
uses for a branch with no pull request. It would send you to `submit` for work that
already had one open. It now tells the two apart.

**`ship` is a local skill.** The default network level on a hosted session reaches package
registries and GitHub, and nothing else. So a deploy command fails on policy rather than
on code. A `Verify:` URL against your own domain fails the same way. Merge from the web if
you like. Run `ship` from your machine.

Nothing here detects the harness. Every rule is written to be true in both places.

## About the hook

`hooks/bash-guard.py` does three things. All are cheap, and all are worth knowing about.

**Trims long check output.** A 500-line test run becomes about 40 lines.

On failure it shows **more**, not less. You get the matching failure lines plus the last
40. A failing command is exactly when you want detail. The exit code is always printed as
`exit=N`.

**Allows the commands it trims.** It has to.

Claude Code checks permissions against the command the hook hands back, not the one Claude
typed. And no `Bash(...)` rule can match a compound statement.

Without this, `npm test` is refused however you write your rules. Claude does not stop
there. It quietly runs `node --test` instead, going around the command your `## Checks`
block named. So the hook carries the decision itself.

Only a single, simple call to a known check runner ever gets that far. The command must
match the built-in list: `npm test`, `pytest`, `cargo test`, `go test`, `tsc`, and
friends. It must contain no `&&`, `||`, `;`, `|`, newline, `$(` or backtick. Anything else
passes through untouched, and faces your normal rules.

This is why `build` and `submit` both insist on running check commands **bare**, one per
call.

A command Claude has already shaped makes the hook stand down. `npm test 2>&1 | tail -20`
is one. You lose the trimming and the `exit=N` line. Claude then works out an exit code by
hand instead. It gets that wrong: `${PIPESTATUS[0]}` after a `;` printed nothing at all in
a real run.

**Asks before committing to the default branch.** It asks rather than blocks. A wrong ask
costs one keypress. A wrong block stops your work.

> ⚠️ **This is an ergonomic speed bump, not a security control.** It matches text in
> command strings. Variable indirection, aliases, or a different binary get past it
> easily. It stops accidents, not attackers. It also fails open. Any error and your
> command runs unchanged.
>
> **Note which way the trimming grant points.** For that narrow set of commands the hook
> *gives* permission rather than withholding it. A hook allow beats your own settings. A
> `"deny": ["Bash(npm:*)"]` entry does **not** stop it. That was tested, not assumed.
> `npm test` runs whatever `package.json` says. So this is a real grant, even if a small
> one. If you would rather keep that decision, drop the `PreToolUse` entry from
> `hooks/hooks.json`. You lose the trimming and get the prompts back.

## Validating changes to this plugin

```bash
claude plugin validate .
```

Changed the hook? Run its contract tests. They take under a second and cost nothing:

```bash
python3 hooks/test-bash-guard.py
```

Changed a skill's frontmatter? Same deal, same second:

```bash
python3 skills/test-frontmatter.py
```

It checks that every `description` reaches the model whole.

In a plain YAML scalar, a `#` preceded by a space opens a comment. So `... like #123 ...`
quietly cut 60 characters off `flow`'s description. That included "This is the entry
point, start here.", the sentence most likely to make the skill fire.

The file read correctly the whole time. Quoting the value fixes it. This test stops it
coming back, and refuses to pass by finding no skills.

Expect **exactly one warning**, about the missing `version` field. That is on purpose.
With no version, `/plugin update` picks up every push. If you set one, updates silently
stop arriving until you remember to bump it.

⚠️ Do **not** use `--strict`. It turns that expected warning into an error. If you ever
see a second warning, something is genuinely wrong.

## What is not here yet

Phase 1 is the smallest useful thing, on purpose. These are left out on purpose too:

- A standalone `plan` skill. Deep work already writes `.devflow/plans/<name>.md` and resumes from it. But there is no way to invoke planning on its own. You cannot revise a plan once written, or tidy up old ones.
- `debug`, the disciplined bug-fixing loop. For now bugs go through `build`.
- Model routing by size. The two agents pin a model. The six skills inherit whatever you are on. `flow` picks Quick, Standard or Deep at runtime. But a skill's `model:` is fixed on disk, and a skill cannot type `/model` at itself. That is the same wall `/code-review` hit. Routing the sizes would mean a skill per size, which is three copies of `flow` to keep matching.
- Cleanup of worktrees and folder copies. `ship` handles branches, dev servers and temp files. Copies of the repo are still yours.
- Capturing lessons.

These are only worth building if two weeks of real use shows you need them. Add each one because you hit the problem, not because it sounded good.

## Borrowed from

Ideas adapted, with thanks:

- **[obra/superpowers](https://github.com/obra/superpowers)** (MIT, and Apache-2.0 as the packaged plugin) — watch the test fail first. Prove it before saying done. The three-size classifier, **with its "never go lighter" rule inverted on purpose**. Never volunteer discard. From `requesting-code-review` and `receiving-code-review`: give the reviewer crafted context and never the session's history. Review the work against its plan. Treat findings as suggestions to evaluate rather than orders to follow. That last one is why `submit` can reject a finding in writing.
- **[mattpocock/skills](https://github.com/mattpocock/skills)** (MIT) — ask every question in one round, with a recommendation attached. Test only at agreed seams. From its `code-review` skill: **the two axes and the refusal to blend them**. Also scope creep as a finding in its own right, proving the fixed point resolves before spawning anything, and reporting "no spec available" rather than inventing requirements. Its twelve-smell baseline was **not** taken. It is judgement-call territory by design, which is the opposite of `reviewer`'s bar.
- **[wshobson/commands](https://github.com/wshobson/commands)** (MIT) — the shape of a git workflow that fits in a few lines.
- **[heliohq/ship](https://github.com/heliohq/ship)** — two ideas, both reworked. Its **independent peer challenger** became `hardcase`, with the defaults inverted. Theirs produces objections. Ours tries to destroy them, and defaults to *falls*. Its evidence hierarchy became the **first-hand / second-hand** test in `submit` step 4 and `ship` step 5. In theirs, L1 is a screenshot or a response body. L2 is an HTTP 200 or "tests passed", and L2 is insufficient. Restated as one question you can apply yourself: *would this have been true before the change?* Its pipeline shape was **not** taken. It runs every job through the full sequence, which is the thing the Quick tier exists to refuse.
- **Anthropic's [`code-review`](https://github.com/anthropics/claude-plugins-official) plugin** (Apache-2.0) — `reviewer`'s "Do not report" list is its false-positive taxonomy, rephrased: pre-existing problems, pedantic nitpicks, anything a linter or typechecker already catches, quality gripes no `CLAUDE.md` asked for. Its confidence filter is **reworked, not copied**. Theirs is a 0-100 score across five bands, dropped below 80. Ours became one question: can you name the input that fails? Its five review lenses were not carried over. `reviewer` uses four of its own.
- **Anthropic's `feature-dev` plugin** (Apache-2.0) — reviewed for patterns only, nothing taken.

## License

MIT. See [LICENSE](LICENSE).
