# A builder agent per piece, so a Deep job does not outgrow one window

Issue: none

## Why

One session builds every piece today. By piece 4 the window is full of piece 1.
Then compaction, which keeps a summary and drops the plan. A fresh agent per
piece keeps the main session small: the plan, and one short report per piece.

## Assumptions

- Pieces run **in order, never in parallel**. Two agents committing to one
  branch at once is a merge conflict with nobody to solve it.
- The `builder` agent pins `model: opus` and `effort: high`. Build is where
  correctness lives (rule 1), so no cheaper model until real runs show it
  is safe. That is a later change, made with evidence.
- The agent can call the `devflow:build` skill through the Skill tool. If a
  subagent turns out not to have it, the agent body inlines the five gates
  instead. Piece 2 finds out which.
- On Pro, the harness refuses to start an agent unless the human asked.
  `flow` asks once, with the same words `review` uses. If the answer is no,
  it builds in-session, exactly as today. Nothing is lost, only the window.
- Quick and Standard do not change. One piece, one session, as now.
- The agent cannot ask the human. "Which seam" and "stuck after three tries"
  become lines in its report. `flow` stops on "stuck" and hands it to the
  human.

## Pieces

1. [independent: yes] Add `Done when:` to each piece in the plan template
   The agent has no session to ask, so it needs to know when to stop. One
   line per piece. Update the template in `flow`, the example in `README.md`
   and `docs/flow.md`.
   Verify: python3 skills/test-frontmatter.py
   Done when: the template in `flow` shows the field, and this plan uses it

2. [independent: no] Add `agents/builder.md`
   Builds one piece from a plan file. Gets the plan path, the piece number,
   and whether the tree is dirty. Runs `devflow:build`. Commits the piece.
   Reports five lines: piece, test output, commit SHA, seam chosen, stuck or
   not. Never asks. Never touches another piece. Never calls `submit`.
   `tools:` needs Read, Edit, Write, Grep, Glob, Bash and Skill. Pins model
   and effort, or `test-frontmatter.py` refuses it.
   Verify: python3 skills/test-frontmatter.py
   Done when: the test passes with the agent present, and a hand-run of the
   agent on a two-piece scaffold commits piece 1 and reports

3. [independent: no] `flow` Deep becomes a coordinator
   After the plan is written, and on resume from step 0b: for each unbuilt
   piece in order, spawn `devflow:builder`. Pass the plan path, the piece
   number, and the dirty flag from step 0b. Read the report. On "stuck",
   stop and say what was ruled out. After the last piece, call `submit` as
   now. On Pro, ask once first; on no, fall through to today's in-session
   path. Rules: never spawn two builders at once, never skip a report.
   Verify: python3 skills/test-frontmatter.py
   Done when: a Deep request on the `full-loop` scaffold spawns one agent per
   piece and ends in `submit`

4. [independent: no] Eval case `evals/deep-coordinator`
   A Deep request with a two-piece plan. Graders: `tool_used` Agent at least
   2, `tool_order` Agent before Skill(submit), a regex for the resume line.
   Cost: high. Mark it so in `evals/README.md` and bump "Seven cases".
   Verify: python3 evals/test-run.py
   Done when: the case parses, `run.py --dry-run` lists it, and one paid run
   passes

5. [independent: no] Docs and provenance
   README size table: Deep row says "one agent per piece". `docs/flow.md`
   gets a short section. `docs/provenance.md` gets a row per idea above,
   with superpowers' subagent-driven-development named as the source.
   Verify: python3 skills/test-frontmatter.py
   Done when: `claude plugin validate .` still prints exactly one warning

## Not in this plan

- Parallel builders in worktrees. Real gain, real complexity. Later, if
  sequential proves too slow.
- A cheaper model for the builder. Needs evidence first.
- Revising a plan mid-job. Still on the "not here yet" list.
