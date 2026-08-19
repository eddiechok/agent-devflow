---
name: build
description: Use when writing or changing code, including fixing a bug. Enforces test-first - write the test, watch it fail for the right reason, then make it pass. Normally started by the flow skill, but safe to invoke directly.
argument-hint: "[what to build, or a piece from the plan file]"
---

# build

Write the test. Watch it fail. Make it pass. Prove it.

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

The bash hook trims long check output and prints `exit=N` itself — but only for
a plain command. Shape it yourself and the hook steps aside by design, and you
lose the trimming *and* the exit line. Doing it by hand is fragile anyway:
`${PIPESTATUS[0]}` after a `;` silently printed nothing in a real run, because
the shell was not the one that syntax assumes.

Arguments are still bare — `pnpm test src/db` is fine. Shell plumbing is not.

## Get off the default branch first

Before the first edit, check where you are:

```
git rev-parse --abbrev-ref HEAD
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main
```

The second one answers with the remote ref, `origin/main`, so compare the first against it with the `origin/` dropped. Do the stripping yourself rather than piping through `sed` — a pipe here costs a permission prompt for `sed` on top of the git command, in every project, forever.

If they match, create the branch now, before touching a file:

```
git checkout -b <type>/<short-name>
```

If they do not match you are already on a branch — **keep it, whatever it is called.** One someone else named, or one a harness created for you, satisfies this step as well as one you would have named. Renaming it can break a harness that pins where you are allowed to push.

`submit` checks this too, but by then it is late. Editing happens here, and `submit` is several gates away — if it never runs because you got stuck, the checks stayed red, or the human stopped you, the edits are left sitting uncommitted on the default branch. Branching first costs one command and the abort case stays clean.

Branching is not committing. Committing happens in one case only — a finished plan piece, below. Everything else is `submit`'s.

## The five gates

Every change goes through these in order. No skipping.

### 1. RED — write the test first

Write the smallest test that fails because the thing you are about to build does not exist yet.

**Test at seams, not at every function.** A seam is a boundary someone else's code calls through: an exported function, an API route, a component's public props. The tell that you went inside one: the test breaks when you refactor, while the behaviour never changed. Reaching round the back counts too — checking the database directly instead of asking the interface what it returns.

If it is not obvious where the seam is, say which one you picked and why, in one line, before writing the test.

**The expected value has to come from somewhere other than the code.** A literal you know is right, a worked example, the spec, a number you did by hand.

A test that works the answer out the same way the code does cannot ever disagree with it:

```js
expect(add(a, b)).toBe(a + b);
```

That one passes verify-RED as well — the function does not exist yet, so it fails, and it fails for the right reason. Every gate goes green and nothing was ever tested. You are the one writing both sides here, which is exactly why this is easy to do by accident.

### 2. Verify RED — watch it fail

Run the test. **Show the output.**

Then check the failure is the *right* failure. A test that fails because of a typo in the import, or because the file does not exist, has proven nothing.

> If you did not watch it fail for the right reason, you do not know it tests anything.

If it passes immediately, the test is wrong. Fix the test before writing any code.

### 3. GREEN — make it pass

Write the smallest code that makes the test pass. Not the general version. Not the version with the options you might want later. The smallest one.

### 4. Verify GREEN — watch it pass

Run the test again. **Show the output.** Then run typecheck.

### 5. Refactor — only now

Clean it up with the test still passing. Run the test again after.

## If code already exists without a test

Do not delete it and start over. That wastes work and fights how people actually explore.

Instead: write a test at its public seam now, and **prove the test is real** by temporarily breaking the code and showing the test fail. Then restore the code. Same guarantee, none of the waste.

## When you get stuck

Count your attempts at the same problem.

**After 2 failed attempts**, stop changing things and say what you have ruled out.

**After 3**, stop and report. Do not try a fourth patch at the same layer — three failures at one layer usually means the problem is somewhere else.

State plainly:
- what you tried
- what each attempt proved is *not* the cause
- what you would look at next

A clear "I am stuck, here is the map" is worth more than a fourth guess.

## Debug markers

If you add temporary logging while working, tag it:

```js
console.log("[DBG-a3f] payload:", payload);
```

Before finishing, run the same sweep `submit` step 3 runs, and remove every hit:

```
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'
```

Word for word the same command, so the two cannot drift apart. No marker may survive into a commit. Markdown is excluded because a marker there is a code sample, not something that runs — `submit` step 3 skips it for the same reason, and keeps the quotes for the same reason too: zsh expands a bare `*.md` and the command dies before grep sees it.

## Commit the piece — only when you were given one

If `flow` handed you a piece from `.devflow/plans/<name>.md`, commit it once it is green, refactored, swept of debug markers and the full suite has run once — then hand back:

```
<type>(<scope>): <the piece, as an imperative subject>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci` — the same list `submit` step 6 uses, and it has to stay the same list.

**This is the only case where `build` commits**, and the reason is narrow. A Quick or Standard change is one piece, and `submit` commits it after the checks and the review, which is where that belongs. A plan is several pieces across a job long enough to outlive the context that started it, and a commit per piece is what makes it resumable: `git log <default branch ref>..HEAD` then answers *which pieces are built* with evidence, rather than a checkbox somebody had to remember to tick.

Commit the piece and nothing else. Not a half-finished next piece, and not unrelated tidying that came along with it.

## Handing back

Say what you built and the output that proves it. Then stop — do not open a PR.

If a skill called you — `flow`, or `tend` fixing what a pull request reported — it takes over from here and submits. Say what you built and stop; do not tell it to run `submit`, it already knows.

If a **human** called you directly, say in one line that the work is ready for `devflow:submit`, and leave that call to them.

## Rules

- Never claim a test passes without showing the output.
- Never add pipes or redirects to a check command. Bare, one per call.
- Never write code before its test.
- Never skip verify-RED because the test "obviously" fails.
- Never let a test work out its expected value the way the code does.
- Never widen scope mid-piece. Finish the piece, then raise the next one separately.
- Never commit anything but a finished plan piece, and never open a PR.
- Run the full test suite once before handing back — not after every edit, and not never. On a plan piece that run is what makes committing it safe, so a five-piece plan runs it five times and that is the price of five trustworthy checkpoints.
