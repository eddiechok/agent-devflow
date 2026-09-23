---
name: build
description: Use when writing or changing code, including fixing a bug. Enforces test-first - write the test, watch it fail for the right reason, then make it pass. Normally started by the flow skill, but safe to invoke directly.
argument-hint: "[what to build, or a piece from the plan file]"
---

# build

Write the test. Watch it fail. Make it pass. Prove it.

Why these rules are what they are: [docs/build.md](../../docs/build.md). Read it only if a
rule looks wrong.

## Find the project's commands

Look for a `## Checks` block in the project's `CLAUDE.md`:

```markdown
## Checks
- Test: pnpm test
- Typecheck: pnpm typecheck
- Lint: pnpm lint
```

If there is no such block, work the commands out from `package.json`, `Makefile`, `pyproject.toml`, `go.mod`, `Cargo.toml` or whatever the project uses — then **tell the human to add the block**, once, in one line. Do not ask permission. Do not guess silently.

Never hardcode a command in this skill. The project is the source of truth.

### Run them bare

Run each command exactly as the `## Checks` block writes it, **one command per
call**. No pipes, no redirects, no `&&`, no `; echo $?`.

If the project's check command is not one the hook recognises, there is no
`exit=N` line and there was never going to be one. Say the outcome in words
instead. Do not write the line yourself.

Arguments are still bare — `pnpm test src/db` is fine. Shell plumbing is not.

## Find the project's words

The project can have a `CONTEXT.md` at its root. Read its `## Words` block. It says what this project's words mean.

Use those words. In test names. In identifiers. In the commit subject.

`build` reads it. `build` never writes it. If a word in it looks wrong, say so when you hand back. Do not fix the file.

No `CONTEXT.md` is normal.

## Get off the default branch first

Before the first edit, check where you are:

```
git rev-parse --abbrev-ref HEAD
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main
```

The second one answers with the remote ref, `origin/main`, so compare the first against it with the `origin/` dropped. Do the stripping yourself rather than piping through `sed`.

**`origin/main` is a fallback, not an answer.** `refs/remotes/origin/HEAD` is only set if
the repo was cloned or somebody ran `git remote set-head`. When it is unset the
`|| echo origin/main` fires and you are **guessing**. If the fallback fired, find the real
default before comparing — `git remote show origin` says it, and so does the forge — or
say in one line that you could not, and branch anyway.

If they match, create the branch now, before touching a file:

```
git checkout -b <type>/<short-name>
```

If they do not match you are already on a branch — **keep it, whatever it is called.**

**One exception, and it is narrow: you were told this is new work.** `flow` decides that,
and only `flow` can. When you were told, cut a fresh branch **from the default branch
ref**, not from where you are standing:

```
git checkout -b <type>/<short-name> <default branch ref>
```

Branching is not committing. Committing happens in one case only — a finished plan piece, below. Everything else is `submit`'s.

Then print the branch, once, before the first edit:

```
✓ **branch** <name>
```

## First: is there anything a test could catch?

The gates below assume behaviour. When there is none, **print one line and skip to the
checks** — run the project's `## Checks` block, show the output, and go on to handing back:

```
– **no-behaviour** README wording — running the checks instead
```

**The bar is narrow, and default to testing.** "I cannot see the seam" is not the same as
"there is no seam" — a config value something reads, a route a page serves, a class a
component applies are all behaviour, and they get a test. Only reach for this when the
change cannot fail at runtime because nothing runs it.

## The five gates

Every change with behaviour goes through these in order. No skipping.

### 1. RED — write the test first

Write the smallest test that fails because the thing you are about to build does not exist yet.

**Test at seams, not at every function.** A seam is a boundary someone else's code calls through: an exported function, an API route, a component's public props. The tell that you went inside one: the test breaks when you refactor, while the behaviour never changed. Reaching round the back counts too — checking the database directly instead of asking the interface what it returns.

If it is not obvious where the seam is, say which one you picked and why, in one line, before writing the test.

**The expected value has to come from somewhere other than the code.** A literal you know is right, a worked example, the spec, a number you did by hand.

A test that works the answer out the same way the code does cannot ever disagree with it:

```js
expect(add(a, b)).toBe(a + b);
```

### 2. Verify RED — watch it fail

Run the test. **Show the output.**

Then check the failure is the *right* failure. A test that fails because of a typo in the import, or because the file does not exist, has proven nothing. Once it is, print:

```
✓ **red** fails for the right reason
```

If it passes immediately, the test is wrong. Fix the test before writing any code.

### 3. GREEN — make it pass

Write the smallest code that makes the test pass. Not the general version. Not the version with the options you might want later. The smallest one.

### 4. Verify GREEN — watch it pass

Run the test again. **Show the output.** Then run typecheck, and print:

```
✓ **green** 1 passed, exit 0
```

### 5. Refactor — only now

Clean it up with the test still passing. Run the test again after.

## If code already exists without a test

Do not delete it and start over.

Instead: write a test at its public seam now, and **prove the test is real** by temporarily breaking the code and showing the test fail. Then restore the code. Same guarantee, none of the waste.

## When you get stuck

Count your attempts at the same problem.

**After 2 failed attempts**, stop changing things and say what you have ruled out.

**After 3**, stop and report. Do not try a fourth patch at the same layer — three failures at one layer usually means the problem is somewhere else.

State plainly:
- what you tried
- what each attempt proved is *not* the cause
- what you would look at next

## Debug markers

If you add temporary logging while working, tag it:

```js
console.log("[DBG-a3f] payload:", payload);
```

Before finishing, run the same sweep `submit` step 3 runs, and remove every hit:

```
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'
```

Word for word the same command, so the two cannot drift apart. No marker may survive into a commit.

## Commit the piece — only when you were given one

If `flow` handed you a piece from `.devflow/plans/<name>.md`, commit it once it is green, refactored, swept of debug markers and the full suite has run once — then hand back:

```
<type>(<scope>): <the piece, as an imperative subject>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci` — the same list `submit` step 7 uses, and it has to stay the same list.

Commit the piece and nothing else. Not a half-finished next piece, and not unrelated tidying that came along with it. Then print:

```
✓ **commit** feat(settings): read the flag in the API (a1b2c3d)
```

## Handing back

Say what you built and the output that proves it. Then stop — do not open a PR.

If a skill called you — `flow`, or `tend` fixing what a pull request reported — it takes over from here and submits. Print `✓ **handback** <what you built>` and stop; do not tell it to run `submit`, it already knows.

If a **human** called you directly, print `✓ **handback** <what you built> — ready for devflow:submit`, and leave that call to them.

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never claim a test passes without showing the output.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never write code before its test.
- Never skip verify-RED because the test "obviously" fails.
- Never let a test work out its expected value the way the code does.
- Never write to `CONTEXT.md`. Read it, use its words, and report a wrong one rather than fixing it.
- Never widen scope mid-piece. Finish the piece, then raise the next one separately.
- Never commit anything but a finished plan piece, and never open a PR.
- Run the full test suite once before handing back — not after every edit, and not never. On a plan piece that run is what makes committing it safe, so a five-piece plan runs it five times and that is the price of five trustworthy checkpoints.
