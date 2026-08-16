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

## The five gates

Every change goes through these in order. No skipping.

### 1. RED — write the test first

Write the smallest test that fails because the thing you are about to build does not exist yet.

**Test at seams, not at every function.** A seam is a boundary someone else's code calls through: an exported function, an API route, a component's public props. Testing internals produces tests that break every refactor and prove nothing.

If it is not obvious where the seam is, say which one you picked and why, in one line, before writing the test.

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

Before finishing, run `grep -rn "\[DBG-" .` and remove every one. No marker may survive into a commit.

## Rules

- Never claim a test passes without showing the output.
- Never write code before its test.
- Never skip verify-RED because the test "obviously" fails.
- Never widen scope mid-piece. Finish the piece, then raise the next one separately.
- Run the full test suite once at the end, not after every edit.
