# evals

Five cases. Run them before you push a change to a skill.

```bash
claude plugin eval . --scaffold --allow-tools Bash Write Edit
```

`--scaffold` is required: every case builds its own throwaway project first,
and scaffold scripts do not run unless you ask for them. `--allow-tools` is
required because the cases need to write files and run commands. Both are
deliberate — the runner will not do either on your behalf.

## What each case is for

| Case | Cost | What breaks if it fails |
|---|---|---|
| `sizing-quick` | low | A typo fix drags the human through questions |
| `sizing-deep` | low | A new subsystem gets built with no plan and no questions |
| `danger-list` | low | Secrets work slips through at Quick with nobody told |
| `setup-writes-checks` | medium | Every downstream check runs a command nobody verified |
| `full-loop` | high | The skills stop handing off to each other |

The first three are the classifier, which is the part of `flow` most likely to
drift and the only part with correction data behind it
(`~/.claude/devflow/overrides.md`). They cut themselves off after a handful of
turns — the size announcement is all they measure, and letting the work run
would multiply the cost for no extra signal.

`full-loop` is the expensive one and earns it. All three bugs found in the
first real end-to-end run lived in the **seams** between skills, not inside
any one of them:

- `flow` never reached `ship`
- `ship` could not tell what the default branch was, so it committed to it
- the bash hook rewrote `npm test` into something no permission rule could
  match, so `build` silently ran a different command instead

None of those are visible from a single skill. Only running the loop finds
them, which is why one case pays for the whole suite.

## Running less

```bash
claude plugin eval . --scaffold --allow-tools Bash Write Edit --tag sizing
claude plugin eval . --scaffold --allow-tools Bash Write Edit --case 'sizing-*'
claude plugin eval . --scaffold --allow-tools Bash Write Edit --runs 1
```

The classifier tags are the cheap everyday loop. Run everything before a
release.

## Reading a failure

Every case carries an `expected_outcome` in plain English. Read that first,
then the grader that failed — the grader names the promise it was checking,
not just the pattern it did not find.

`--runs 3` is the default and it is not padding. Watching the same request
three times produced two different but equally valid implementations, so a
single green run proves less than it looks. A case that passes twice and fails
once is a real finding about the skill, not noise to re-roll.

## Ablation

Pointing the runner at a path (`.`) runs one arm. Pointing it at the installed
plugin adds a no-plugin baseline and reports the delta:

```bash
claude plugin eval devflow@eddiechok-devflow --scaffold --allow-tools Bash Write Edit
```

Worth it for the sizing cases, where the question "does the plugin change
anything?" has a real answer. Not worth it for `full-loop` — without the
plugin there is no `flow` to call, so the baseline arm measures nothing.

## Adding a case

Add one when something breaks in real use, not when it sounds good. The same
rule the plugin applies to itself. A case that has never corresponded to a
real failure is a bill you pay on every run forever.

Copy the nearest existing directory. Prefer `regex`, `tool_used`,
`tool_order` and `file_exists` graders over `llm` ones — they cost nothing,
they never drift, and most promises in these skills are mechanical enough to
check that way. Reach for an `llm` grader only when the promise genuinely is
about judgement, as with test-first ordering.

One trap worth knowing: **`tool_used` counts attempts, not successes.** A
command that was refused still counts as used. `full-loop` was written with a
`tool_used` grader meant to catch the hook blocking `npm test`, and it passed
on a transcript where every `npm test` was denied. When what you care about is
that a command *ran*, assert on something only a real run produces — output it
prints, a file it writes — rather than on the call being made.

Check a new grader both ways before trusting it. Point it at a transcript
where the skill did the right thing **and** one where it did not; a grader
that cannot fail is worse than no grader, because it reads as coverage.
