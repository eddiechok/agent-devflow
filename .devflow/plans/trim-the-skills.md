# Trim the skills

Move the "why" prose out of every `skills/*/SKILL.md` into a docs page per skill, so
the skill holds only its steps and rules. Add a Quick exit to `review` for changes with
no behaviour.

## Assumptions

- One docs page per skill. `docs/flow.md` and `docs/review.md` already exist and are
  extended. `docs/build.md`, `docs/submit.md`, `docs/ship.md`, `docs/tend.md` and
  `docs/setup.md` are new.
- Moved text goes **verbatim**. Headings may be added to stitch paragraphs together.
  Nothing is reworded, shortened or dropped. Every paragraph removed from a skill must
  be findable, word for word, in that skill's docs page.
- Inside a skill, a rule keeps at most one short clause of reason (a half line). Any
  reasoning one full sentence or longer moves. The test for a paragraph: delete it, and
  ask whether the model can still do the step. If yes, it is a why paragraph and it
  moves. If no, it is an instruction and it stays.
- Each trimmed skill links its docs page **once**, near the top, in this shape:
  `Why these rules are what they are: [docs/<skill>.md](../../docs/<skill>.md). Read it only if a rule looks wrong.`
- Step headings, numbered steps, code blocks the model runs, the shapes it prints, and
  every bullet under `## Rules` stay in the skill. Frontmatter is untouched.
- `review` learns "no behaviour" only from a line `submit` passes down,
  `no-behaviour: <build's reason>`. It never decides from file types, because in this
  repo a `.md` skill file is behaviour.
- The four `agents/*.md` files are not touched.
- The eval cases and their graders are not touched. `evals/README.md` is updated only
  where it cites a line number in a skill that moved.

## Pieces

1. [independent: yes] Add the no-behaviour Quick exit to `review`, fed by `submit`
   Files: `skills/submit/SKILL.md` step 5, `skills/review/SKILL.md`, `docs/review.md`,
   `README.md` (the `review` row in the skills table).
   `submit` step 5: when `build` said `No behaviour to test — <reason>` for this change,
   pass `review` a line `no-behaviour: <reason>` after the fixed point and the request.
   `review`: a new section before step 3. If `$ARGUMENTS` carries `no-behaviour:`, spawn
   no agent. Print one line, `review skipped — no behaviour: <reason>`, and in the step 4
   report write `skipped — no behaviour` under each of Built right, Challenged and Right
   thing, and in Worst of each. This is a third state, distinct from `NOT RUN` and from
   `none`. `submit` treats it as: nothing to fix, and writes `Review: skipped, no
   behaviour` under Evidence in the PR body. Say in `review` that `no-behaviour:` is a
   line `submit` passes and never something `review` works out from the diff.
   Verify: python3 skills/test-frontmatter.py
   Done when: `skills/review/SKILL.md` has a section that, given `no-behaviour:` in its
   arguments, starts no agent and reports all three sections as `skipped — no behaviour`;
   `skills/submit/SKILL.md` step 5 passes that line when `build` said no behaviour and
   step 8's Evidence example shows the skipped form; `docs/review.md` and the `review`
   row of `README.md` mention the exit; all three test commands and
   `claude plugin validate .` pass with the one expected warning.

2. [independent: no] Trim `flow`
   Move every why paragraph from `skills/flow/SKILL.md` into `docs/flow.md`, verbatim,
   under headings that follow the skill's step order. Add the docs link near the top.
   The paragraph about injected Context lines being single commands moves too.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/flow/SKILL.md` appears word for word in
   `docs/flow.md`; the skill keeps every step heading, every code block, every printed
   shape and every `## Rules` bullet; the skill links `docs/flow.md` once; the checks pass.

3. [independent: no] Trim `build`
   Same rule. New page `docs/build.md`.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/build/SKILL.md` appears word for word in
   `docs/build.md`; the skill keeps every gate heading, code block, printed shape and
   `## Rules` bullet; the skill links `docs/build.md` once; the checks pass.

4. [independent: no] Trim `submit`
   Same rule. New page `docs/submit.md`. Piece 1's additions are kept as instructions.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/submit/SKILL.md` appears word for word
   in `docs/submit.md`; the skill keeps every numbered step, code block, the PR body
   template and every `## Rules` bullet; the skill links `docs/submit.md` once; the
   checks pass.

5. [independent: no] Trim `review`
   Same rule. Extend `docs/review.md`. Piece 1's Quick exit stays as instruction.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/review/SKILL.md` appears word for word
   in `docs/review.md`; the skill keeps every step, the report template and every
   `## Rules` bullet; the skill links `docs/review.md` once; the checks pass.

6. [independent: no] Trim `ship`
   Same rule. New page `docs/ship.md`. The two real merge-error runs and the
   `ls-remote` reasoning move; the table of the two runs and the commands stay.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/ship/SKILL.md` appears word for word in
   `docs/ship.md`; the skill keeps every numbered step, the error table, every code
   block, the report shape and every `## Rules` bullet; `disable-model-invocation: true`
   is still in its frontmatter; the skill links `docs/ship.md` once; the checks pass.

7. [independent: no] Trim `tend` and `setup`
   Same rule. New pages `docs/tend.md` and `docs/setup.md`.
   Verify: python3 skills/test-frontmatter.py
   Done when: every paragraph removed from `skills/tend/SKILL.md` and
   `skills/setup/SKILL.md` appears word for word in `docs/tend.md` and `docs/setup.md`
   respectively; each skill keeps every step, code block, printed shape and `## Rules`
   bullet; each links its page once; `setup` still carries
   `disable-model-invocation: true`; the checks pass.

8. [independent: no] Point the index at the new pages
   `README.md` "More" table: one row per new docs page, and the existing `docs/flow.md`
   and `docs/review.md` rows updated to say they now hold the why text. `evals/README.md`
   lines 50-53 cite line numbers in `skills/flow/SKILL.md` for the two worked examples;
   re-read the trimmed file and correct the numbers.
   Verify: python3 evals/test-run.py
   Done when: every file under `docs/` is listed in the README "More" table; the line
   numbers cited in `evals/README.md` match `grep -n "Quick — single-file copy change"`
   and `grep -n "Deep — new subsystem"` on `skills/flow/SKILL.md`; the checks pass.
