# devflow

One dev loop for features, changes, bug fixes and chores. Sizes the work, tests first, proves it runs, opens a PR. Asks you as little as possible.

This is **Phase 1** — deliberately small. See [What is not here yet](#what-is-not-here-yet).

## The three rules

In order. When two disagree, the higher one wins.

**1. Be correct, above everything else.** If the work is wrong, nothing else matters. When being cheap causes work to be redone, that is a correctness problem wearing a cost costume, not a cost decision.

**2. Ask as little as possible, but not less than that.** Zero questions is not the goal. The fewest interruptions, placed where they matter most, is the goal.

**3. Be cheap where it is a real trade.** Never cheap on code review, hard bugs, or anything on the danger list.

## Install

```bash
/plugin marketplace add eddiechok/agent-devflow
/plugin install devflow@eddiechok-devflow
```

Or install it everywhere at once by adding this to `~/.claude/settings.json`:

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

Add a `## Checks` block to the project's `CLAUDE.md`. This is the **only** thing each project must provide, and it is what makes devflow work with any language:

```markdown
## Checks
- Test: pnpm test
- Typecheck: pnpm typecheck
- Lint: pnpm lint
```

No commands are hardcoded in this plugin. The project is the source of truth.

## Use it

```
/devflow:flow add a settings page for email alerts
/devflow:flow #123
/devflow:flow --deep change how sessions are stored
```

`flow` sizes the work and routes it. You should not normally need to call the others directly.

| Size | For | What happens |
|---|---|---|
| **Quick** | Typos, chores, most bug fixes | Straight to building. No questions. |
| **Standard** | Changing existing behaviour | Questions only if genuinely unclear. |
| **Deep** | New features, wide refactors | One round of questions, then a written plan. |

It announces the size in one line before doing anything, so you can disagree immediately.

### If it sizes something wrong

```
/devflow:flow --deep <request>
/devflow:flow --quick <request>
```

Overrides are recorded to `.devflow/overrides.md`. Each one is a real example of a misclassification, which is far better test data than invented ones. Do not delete the file.

## The skills

| Skill | What it does |
|---|---|
| `flow` | Sizes the request, routes it, asks any questions in one batch |
| `build` | Test first, watch it fail for the right reason, then make it pass |
| `ship` | Runs the checks fresh, runs the app, commits, opens the PR. **Never merges.** |

## When it will ask you

**Direction** — Deep jobs always, Standard only when genuinely unclear, Quick never. All questions come at once, each with a recommended answer. `yes to all` is a valid reply. Anything you skip takes the recommendation and appears in the PR under **Assumptions**.

**Merge** — always yours. `ship` opens the PR and stops.

**Committing to the default branch** — the hook asks first.

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

## About the hook

`hooks/bash-guard.py` does two things, both cheap and both worth knowing about:

**Trims long check output.** A 500-line test run becomes about 40 lines. On failure it shows **more**, not less — the matching failure lines plus the last 40 — because a failing command is exactly when you want detail. The exit code is always printed as `exit=N`.

**Asks before committing to the default branch.** It asks rather than blocks. A wrong ask costs one keypress; a wrong block stops your work.

> **This is an ergonomic speed bump, not a security control.** It matches text in command strings and is trivially bypassed by variable indirection, aliases, or a different binary. It stops accidents, not attackers. It also fails open: any error and your command runs unchanged.

## Validating changes to this plugin

```bash
claude plugin validate .
```

Expect **exactly one warning**, about the missing `version` field. That is deliberate: with no version, `/plugin update` picks up every push. If you set one, updates silently stop arriving until you remember to bump it.

Do **not** use `--strict` — it turns that intentional warning into an error. If you ever see a second warning, something is genuinely wrong.

## What is not here yet

Phase 1 is deliberately the smallest useful thing. Deliberately absent:

- `plan` — writing plans to a file. For now `flow` asks its questions inline.
- `debug` — the disciplined bug-fixing loop. For now bugs go through `build`.
- `tend` — handling CI failures and review comments after the PR opens.
- `release` — checking the deploy actually worked.
- `reviewer` and `hardcase` agents — for now `ship` uses the built-in `/code-review`.
- Cleanup of branches, folder copies and dev servers.
- Capturing lessons.

These are only worth building if two weeks of real use shows you need them. Each one that gets added should be added because you hit the problem, not because it sounded good.

## Borrowed from

Ideas adapted, with thanks:

- **[obra/superpowers](https://github.com/obra/superpowers)** (MIT) — watch the test fail first; prove it before saying done; the three-size classifier, **with its "never go lighter" rule deliberately inverted**; never volunteer discard.
- **[mattpocock/skills](https://github.com/mattpocock/skills)** (MIT) — ask every question in one round with a recommendation attached; test only at agreed seams.
- **[wshobson/commands](https://github.com/wshobson/commands)** (MIT) — the shape of a git workflow that fits in a few lines.
- **Anthropic's `feature-dev` plugin** — reviewed for patterns only. Not copied: it is all rights reserved. The confidence-threshold idea for review findings is reimplemented, not lifted.

## License

MIT. See [LICENSE](LICENSE).
