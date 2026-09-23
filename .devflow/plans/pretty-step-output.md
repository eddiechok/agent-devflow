# Pretty step output: one marked line per step

Issue: none

## Why

Each step's output has no common shape today. Some steps print `label: text`,
some print prose, and some main-path steps print nothing, so a skipped step looks
like a clean one. The human wants one line per step, in one shape, easy to scan.

## The shape

```
✓ **checks** 3 of 3 pass, exit 0
```

- A mark, a bold one-word lowercase label, then the result.
- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- Each line stands alone, with a blank line before and after it, so markdown does
  not join two lines into one paragraph. No column padding — the desktop app uses
  a proportional font, so padding collapses; the bold label does that job.
- A block of several lines (ship's summary, setup's summary, tend's check list)
  is the same shape, one line each, blank lines between.

## Assumptions

- Human-facing lines only: flow, build, submit, review, tend, ship, setup. Agent
  reports (builder, reviewer, hardcase, spec-reviewer) stay as they are — only the
  model reads them, and flow and submit parse them.
- The flow size line (`Standard — tighten the export copy.`) stays exactly as it
  is. It is the header of the run, and many evals match it.
- Hand-off arguments are not printed lines and do not change: `request:`,
  `no-behaviour:`, the `Also parked as` chip line, the `Backlog:` commit line.
- review's report template (`## Built right`, `## Challenged`, …) does not change.
  submit parses it. Only review's one-line status lines take the shape.
- The PR body does not change.
- flow's deliberate "print nothing" silences stay silent. The main-path steps of
  build and submit that are silent today get a line (branch, test, commit, debug).
- Change the printed lines, never gloss words in the skill prose. The skill text
  keeps its internal words; only what is printed changes (the `tested at:` rule).
- Every changed line is re-pinned in the test or eval grader that pinned it
  before, and any skill that reads a changed line (submit reads flow's plan line
  and build's no-behaviour line) is updated in the same piece. Re-pinning is not
  weakening: each pin must still fail on the old line.
- `evals/test-run.py` pins the flow size-line examples by line number in
  `evals/README.md`. Any piece that moves those flow lines updates the README.
- No eval is run. `python3 evals/run.py` costs money; graders are updated by hand
  and `evals/test-run.py` keeps them honest.
- One chain. Every piece re-pins in `skills/test-frontmatter.py`, a shared file,
  so the pieces cannot run side by side.

## Pieces

1. [independent: no] chain: A — Add the shape as a short `## Output` section to all seven human-facing skills
   Same text in each: the mark, the bold label, the three marks and what they
   mean, one line per step, blank lines between. No examples beyond one line.
   Add a test that every one of the seven skills carries it word for word.
   Verify: python3 skills/test-frontmatter.py
   Done when: all seven SKILL.md files have the identical `## Output` section and the test fails if any one drops or changes it

2. [independent: no] chain: A — flow prints every line in the shape
   Every printed line in `skills/flow/SKILL.md` — worktree, backlog, features,
   parked, chips, glossary, plan, settings, chains, override, the per-chain report
   (keep `tested at:` as its label) — and "no PR, fresh branch". Not the size
   line. Update the pins in `skills/test-frontmatter.py`, the trace graders in
   `evals/*/case.yaml` that match these lines, `evals/README.md` line numbers,
   the quotes in `docs/flow.md`, and submit's reference to the plan line.
   Verify: python3 skills/test-frontmatter.py && python3 evals/test-run.py
   Done when: flow's `plan` line reads `✓ **plan** #45`, every flow line pinned before is pinned in the new shape, and both tests pass

3. [independent: no] chain: A — build and submit print one line per step
   build: branch, test (red then green), no-behaviour, commit, handback.
   submit: branch, checks, debug, live, review, docs, final look, commit, pr (new
   or updated), second opinion. The steps silent today now print. Update submit's
   reading of build's no-behaviour line, the pins, the graders, and the quotes in
   `docs/submit.md` and `docs/review.md`.
   Verify: python3 skills/test-frontmatter.py && python3 evals/test-run.py
   Done when: a normal submit run prints nine shaped lines, `– **docs** nothing stale` is pinned, and both tests pass

4. [independent: no] chain: A — review, tend, ship and setup print in the shape
   review: skipped, reviewer clean, agents-not-permitted. tend: the check list
   and the final report. ship: the status block, conflict, no checks, the final
   summary (`Merged`, `Tended`, `Retargeted`, `Deploy`, `Live`, `Cleaned`,
   `Session`). setup: pass/fail per command and the final summary. Update the
   pins (`Tended:`, `Retargeted:`, `conflict: handing #`, the `Plans: github`
   summary line) and the graders, including the one `evals/test-run.py` requires.
   Verify: python3 skills/test-frontmatter.py && python3 evals/test-run.py && claude plugin validate .
   Done when: ship's summary prints as `✓ **merged** #2 (rebase), remote branch deleted` and the rest in the shape, every old pin is re-pinned, and all three commands pass with only the version warning
