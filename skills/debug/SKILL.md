---
name: debug
description: Use when a bug's cause is not known - nobody can point at where it is. Builds a red-capable one-command loop, reproduces and shrinks the bug, ranks 3 to 5 falsifiable causes, then probes them one at a time until one is confirmed. Only finds the cause - the fix goes to build, with the confirmed cause and the red command as its first failing test. Normally started by the flow skill, but safe to invoke directly.
argument-hint: "[the bug, in the human's own words, or a piece from the plan file] [what has already been tried, if anything]"
---

# debug

Find the cause. Prove it. Hand it to `build`.

Why these rules are what they are: [docs/debug.md](../../docs/debug.md). Read it only if a
rule looks wrong.

## What this skill does, and does not

**`debug` only finds the cause. It never writes the fix.** The one command that shows the
bug becomes `build`'s first failing test — one test-first loop, not two. Fixing here would
mean the fix goes untested, or `build` tests it a second time from nothing, throwing away
the loop this skill just built.

A bug that can already be pointed at — the file, the function, the line — has no cause left
to find, and goes to `build` directly, on `build`'s own test-first loop, same as any other
change. `debug` exists for the other kind: a report with no known location.

## Phase 1 — build a red-capable loop

**This phase is the skill. Everything after it is mechanical.** A tight loop that goes red
on this exact bug turns every later phase into reading its output. No loop, and the phases
after this one are staring at code and guessing.

Build **one command** — a failing test at whatever seam reaches the bug, a script against a
running dev server, a CLI call diffed against a known-good output, a replayed captured
request, a small throwaway harness — whatever reaches the bug fastest. Run it once. It has
to be:

- **Red-capable** — it drives the actual code path and asserts the reported symptom, so it
  can go red on this bug and green once it is fixed. "Runs without erroring" is not this.
- **Deterministic** — the same verdict every run. A bug that only sometimes reproduces gets
  the trigger looped until the rate is high enough to debug against, not called "flaky" and
  left alone.
- **Fast** — seconds, not minutes, so the phases ahead of it can afford to run it many times.

### When no loop can be built

**Stop, and ask the human.** Say what you tried, and ask for one of: a log, access to the
environment that reproduces it, or a way to trigger it yourself. Never guess a cause
without a command that has actually gone red on it — that is the one thing this skill
exists to prevent.

## Phase 2 — reproduce and shrink

Run the loop again and confirm it shows the symptom that was reported, not a different
failure that happened to be nearby — the wrong bug is worse than no bug. Then shrink the
scenario: cut inputs, callers, config and steps one at a time, re-running the loop after
each cut, keeping only what is load-bearing for the failure. Stop cutting when everything
left makes the loop go green if removed.

A smaller repro narrows the hypotheses in the next phase, and becomes the seam for
`build`'s regression test in the phase after that.

## Phase 3 — rank 3 to 5 falsifiable causes

Write down 3 to 5 candidate causes before testing any of them — one hypothesis, tested
right away, anchors on whatever came to mind first. Each one states a prediction that could
turn out false:

> If `<cause>` is why this happens, then `<changing one thing>` makes the bug disappear.

A line with no prediction is a guess, not a hypothesis. Sharpen it or drop it.

**Show the ranked list, and carry on — do not wait for the human to answer.** They may know
more ("we deployed a change to #3 yesterday"), and a reply can still re-rank the list, but
nothing here blocks on it.

## Phase 4 — probe one at a time

Test the top-ranked prediction first. Change one variable, run the loop, read the result.
If the prediction fails, move to the next hypothesis — never stack a second probe on top of
one that has not been confirmed.

Prefer a debugger or REPL inspection over a log where the environment supports one. Where a
log is the only option, tag every line so the cleanup at the end is one grep:

```
console.log("[DBG-a3f] payload:", payload);
```

Before handing back, run the same sweep `submit` step 3 runs, and remove every hit:

```
grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'
```

## Phase 5 — the confirmed cause

A cause is confirmed once its prediction held: the change you made produced exactly the
change it predicted, on the loop from Phase 1. Restate it in one sentence, naming the
prediction that confirmed it.

## Handing back

Report two things and nothing else:

- **The cause** — one sentence, with the prediction that confirmed it.
- **The red command** — the loop from Phase 1, already shrunk in Phase 2, ready to become
  `build`'s first failing test.

If `flow` called this skill, it takes over from here: it calls `build` with the cause and
the red command, then `submit`. Print `✓ **handback** <the cause>` and stop — do not call
`build` yourself.

If a human called it directly, print `✓ **handback** <the cause> — ready for devflow:build`,
and leave that call to them.

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **loop** tests/checkout.spec.js -t "empty cart" (2s, red)`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per phase, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the report.

## Rules

- Never propose a fix. That is `build`'s loop, not this one.
- Never guess a cause without a command that has gone red on it.
- Never confirm a hypothesis whose prediction was never stated.
- Never wait on the human for the ranked list of causes — show it and carry on.
- Never stop reproducing on a failure that is not the one reported.
- Never stack an untested probe on top of another. One variable at a time.
- Never leave a `[DBG-` marker in what you hand back. Sweep before the handback line.
- Never hand `build` anything but the cause and the red command.
