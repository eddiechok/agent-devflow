---
name: flow
description: "Use when a request will change anything tracked in the repo - a feature, a bug fix, a refactor, a chore or a dependency bump, and equally copy, content, docs, config, styles, images or other assets. Editing a tracked file is the test, not whether the work sounds like coding. Enter here mid-task too, the moment an investigation turns into an edit. Sizes the work as Quick, Standard or Deep, then routes it through build and submit, so the work ends as a pull request rather than uncommitted changes. Accepts free text, a GitHub issue number like #123, or an issue URL. This is the entry point, start here."
argument-hint: "[--quick|--deep] what you want, or #123"
allowed-tools: Bash(git status:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(gh issue view:*)
---

# flow

Size the work, then route it. One line before anything else.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- Status: !`git status --short 2>/dev/null | head -20 || true`

## Step 1 — get the request

`$ARGUMENTS` is the request.

If it starts with `#` or is a GitHub issue URL, read the issue first — `gh issue view NUMBER`, or whatever GitHub access this environment has. The issue body is the request. Remember the number so `submit` can close it.

If you cannot read it, **ask for the request in words**. A number you could not open is not a request, and sizing one you guessed at is worse than asking.

If `--quick` or `--deep` is present, that is the size. Skip step 2, and **record the override** — see "Recording overrides" at the end. Do not argue with an explicit override.

## Step 2 — size it

Pick one. Default **down**. Only go heavier when there is a concrete reason.

| Size | Use when | What it means |
|---|---|---|
| **Quick** | Typo, rename, config value, doc fix, dependency bump with no breaking changes, a bug in code you can already point at | No planning, no questions |
| **Standard** | Changing behaviour of code that already exists, one clear seam, you know roughly where it goes | Questions only if genuinely unclear |
| **Deep** | New feature, new subsystem, a change across many files, or you cannot name the files it touches yet | One round of questions, then a written plan |

**Upgrade from Quick to Standard the moment** the change reaches a second file you did not expect, or you cannot state the fix in one sentence.

### The danger list — always at least Standard

If the work touches any of these, use **at least Standard**, ask the human, and say plainly that a security review is worth running:

- login, permissions, sessions, or anything auth
- passwords, API keys, tokens, secrets
- payments or billing
- database schema or data migrations
- a public API or wire format other people depend on
- CI/CD configuration
- deleting or weakening existing tests
- anything the change cannot be reverted out of

Say which item matched.

## Step 3 — announce it

Exactly one line, before any other output:

```
Quick — single-file copy change.
```

```
Deep — new subsystem, touches auth (danger list).
```

Eight words of reason or fewer. Then continue without waiting.

If you arrived here mid-turn, because a question or an investigation turned into a change, announce it **before the first edit** instead. Same rule, measured from the work rather than from the conversation: nothing gets edited before a size is on screen.

## Step 4 — route it

**Quick** → go straight to `devflow:build`. No questions.

**Standard** → if anything is genuinely ambiguous, ask **one** round of questions (see below), then `devflow:build`. If nothing is ambiguous, go straight to `devflow:build`.

**Deep** → ask one round of questions, get agreement, then work through the pieces with `devflow:build`, one at a time.

Every size then goes on to step 5. `build` finishing is not the job finishing.

### Asking questions — one round only

When you need input, ask **everything you can answer now, in one numbered list**. Never drip-feed one question per turn.

Only ask what you genuinely cannot determine yourself. Read the code first. A question you could have answered by opening a file is a wasted interruption.

Give every question a recommended answer:

```
1. Should this replace the existing export, or sit alongside it?
   -> Recommend: replace. Nothing else imports it.

2. Store the flag per-user or globally?
   -> Recommend: per-user, matching how notifications already work.

Reply "yes to all" to take every recommendation.
```

Anything the human does not answer takes the recommendation, and **goes into the PR body under "Assumptions"** so it can be checked at merge time instead of blocking now.

### Deep only — write the plan down

Split the work into pieces. Each piece must be:

- **One reviewable change.** Size it by what makes a sensible diff, not by what fits in memory.
- **Marked as depending on another piece, or not.**

"Independent" is stricter than "different files". Two pieces are only independent if **neither depends on a design decision the other makes**. Two unrelated endpoints, independent. One defines a type the other consumes, **not** independent — both will finish, both will pass their own tests, and it will break when they are joined.

Write it to `.devflow/plans/<short-name>.md`:

```markdown
# <what this is>

Issue: #123 (if there is one)

## Assumptions
- Took the recommendation on X because no answer was given

## Pieces
1. [independent: no] Add the storage column and migration
   Verify: pnpm test src/db
2. [independent: no] Read it in the settings API
   Verify: pnpm test src/api/settings
```

Build one piece at a time, in order.

The plan file is the spec `review`'s second axis reads, not a progress tracker: nothing writes back to it, and nothing commits between pieces. **Do not `/clear` mid-plan** — the file cannot tell you which pieces are built, and neither can `git log`.

## Step 5 — submit it

When `build` comes back — after the last piece, if there were several — call `devflow:submit` yourself, in the same turn.

Do not stop at "ready for a PR" and hand it back. `build` deliberately does not know about submitting, so if you do not make this call nobody does, and the work sits finished-but-uncommitted on a dirty working tree.

The only reasons not to call `submit`:

- The build did not reach green. Say what is red and stop.
- The human said not to.

Both are things you say out loud. Neither is silence.

## Recording overrides

If the human used `--quick` or `--deep`, they are correcting a mistake this skill would have made. That is free labelled test data and it should not be lost.

**Write it outside the project**, to `~/.claude/devflow/overrides.md`, creating the directory and file if missing.

Global on purpose. These are notes about **this plugin**, not about the project you happen to be in. Kept per-project they would scatter across every repo you work in, get committed into unrelated projects, and be impossible to review together — which is the only way they are useful.

Work out your own size first, so the record shows what would have happened:

```
- 2026-08-16 | myapp | "fix the login redirect" | guessed: Quick | correct: Deep
```

Include the project name. Patterns show up across repos.

Do not discuss it, do not ask about it. Record it and carry on with the size the human asked for.

## Rules

- Never start with a question. Announce the size first.
- Never go up a size without naming the reason.
- Never do work that the size you announced does not call for.
- Never finish without calling `submit`, or saying in one line why you did not.
- Never call `devflow:ship`. The open PR is where this loop ends; merging is the human's, and only they start it.
- If the human overrules you, they are right. Record it and move on.
