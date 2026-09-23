# Output polish: recap, red/green, fixed labels, 80-character lines

Issue: none — follow-up on PR #38 (pretty-step-output)

## Why

PR #38 gave every printed line one shape, `✓ **label** result`. Four gaps are left:
the step lines are scattered between tool output, so a run is hard to read at the
end; build's expected red test prints `✗`, which reads as a failure; each skill picks
its own labels, so they can drift; and some lines are long enough to wrap.

## Assumptions

- The label list lives only in `skills/test-frontmatter.py`, never in the skill text.
  The test reads every shaped line in the seven human-facing skills and fails on a
  label that is not in the list. The skills stay short because the model reads them
  on every run.
- The 80-character limit counts what the reader sees: the `**` marks do not count, and
  a `<placeholder>` counts as its own length. The `## Output` section states the rule
  in one line. The test checks every shaped example line in the seven skills.
- The recap goes at the end of submit, in one block, just before the PR link. It
  repeats this run's step lines in order and adds no new text.
- build's gate lines become `✓ **red** fails for the right reason` and
  `✓ **green** 1 passed, exit 0` — the words the human asked for.
- Everything PR #38 decided still holds: human lines only, the flow size line and agent
  reports unchanged, hand-off args unchanged, no paid eval run, every changed pin still
  fails on the old line.
- One chain. Every piece edits `skills/test-frontmatter.py`, so the pieces run in order.

## Pieces

1. [independent: no] chain: A — build prints red and green as their own labels
   Replace build's `✗ **test** red …` and `✓ **test** green …` lines with
   `✓ **red** fails for the right reason` and `✓ **green** 1 passed, exit 0`.
   Update any doc or eval that quotes the old lines. Pin both new lines.
   Verify: python3 skills/test-frontmatter.py
   Done when: build's gate lines read `✓ **red**` and `✓ **green**`, and the pins fail on the old `**test**` lines

2. [independent: no] chain: A — submit ends with a recap of the run's step lines
   At the end of submit, just before the PR link, print every step line this run
   printed, in order, in one block, with nothing new added. Say it in submit's step 9.
   Update `docs/submit.md` if it describes how submit ends. Pin the rule.
   Verify: python3 skills/test-frontmatter.py
   Done when: submit's step 9 tells the model to print the recap block before the PR link, and a test fails without it

3. [independent: no] chain: A — one fixed label list, checked by a test
   Add a label list to `skills/test-frontmatter.py`, one label per step, each label
   lowercase and one word. The test finds every shaped line (`✓`, `✗` or `–`, then
   `**label**`) in the seven human-facing skills and fails on a label that is not
   in the list. Rename any label that does not fit, in the skills and in the pins,
   graders and docs that quote it.
   Verify: python3 skills/test-frontmatter.py && python3 evals/test-run.py
   Done when: every shaped line in the seven skills uses a listed label, and the test fails when a skill uses an unlisted one

4. [independent: no] chain: A — no printed line is longer than 80 characters
   Add one line to the shared `## Output` section, the same in all seven skills: keep
   each line to 80 characters; detail goes on the next line or in the PR. Update the
   word-for-word pin. Add a test that checks every shaped example line in the seven
   skills is 80 visible characters or fewer (`**` not counted, a `<placeholder>` counted
   as written). Shorten each line that fails. Update any pin, grader or doc that quotes
   a line you shortened, and `evals/README.md` if flow's size-line examples move.
   Verify: python3 skills/test-frontmatter.py && python3 evals/test-run.py && claude plugin validate .
   Done when: the `## Output` section states the limit in all seven skills, every shaped example line is 80 visible characters or fewer, and all three commands pass with only the version warning
