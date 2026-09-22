# Parallel builders in worktrees, by chain

Today a Deep job runs one `builder` agent per plan piece, strictly in order. A run of
eight pieces took 43 minutes; six of them did not depend on each other. This plan makes
`flow` group pieces into chains, run chains in parallel in git worktrees, and merge the
chain branches back before `submit`.

Base branch: `feat/review-no-behaviour-exit` (PR #23). This work stacks on it, because it
edits `skills/flow/SKILL.md` and `docs/flow.md`, which #23 rewrote. The PR opens with
that branch as its base.

## Assumptions

Decisions the human made:
- Stack on PR #23. Branch `feat/parallel-chains` is cut from `feat/review-no-behaviour-exit`,
  and the PR's base is that branch, not `main`.
- Chain branches merge into the feature branch with `git merge --no-ff`. One merge commit
  per chain. The builders' commit SHAs stay as reported.
- At most **4 chains run at once**. Further chains wait for a slot.
- The builder's model becomes **`sonnet`** (Sonnet 5). The human chose this against the
  builder-per-piece plan's "a cheaper model needs evidence first" line. Effort stays `high`.

Design fixed here so pieces can be built without asking:
- **A chain** is a set of pieces that depend on each other, built in order. An independent
  piece is a chain of one. A chain holds at most 4 pieces. Each piece in the plan carries a
  `chain:` letter, `A`, `B`, `C`... Pieces in one chain are listed in build order.
- **Two chains never edit the same file.** A piece that must touch a file another chain
  touches goes in a **final chain**, marked `chain: final`, which runs alone after every
  other chain has merged.
- **The builder takes a chain, not a piece.** Its three inputs become: the plan body,
  pasted in full (not a path: a worktree does not see the main tree's untracked plan
  file); the chain letter; and `clean` or `dirty`. It builds the chain's pieces in order
  and commits each one, exactly as `build` commits a piece today.
- **The builder's report** is one `branch:` line first, naming the branch it committed on,
  then the same five lines per piece as today: `piece`, `test`, `commit`, `seam`, `stuck`.
  A chain of three pieces returns sixteen lines. `stuck: yes` on a piece ends the chain
  there; later pieces of that chain are not attempted and are not reported.
- **Worktree per builder** comes from `isolation: worktree` in `agents/builder.md`'s
  frontmatter. The harness cuts the branch from the branch `flow` is standing on and
  names it; the builder reads its own name with `git rev-parse --abbrev-ref HEAD` for the
  `branch:` line.
- **A fresh worktree may lack installed dependencies.** If the project's checks fail only
  because of that, the builder installs them once, the way the lockfile implies, says so
  in one line, and carries on. It never edits the lockfile.
- **The merge is local.** `flow` merges chain branches into the feature branch on the
  human's machine. This is not a pull request merge, and it does not touch the default
  branch; `submit` and `ship`'s promises are unchanged. Before each merge:
  `git merge-tree --write-tree <feature> <chain>`; a non-zero exit is a conflict, and
  `flow` stops, names the two chains and the files, and hands it to the human. It never
  resolves a conflict itself.
- **Cleanup.** After a chain merges, `flow` removes its worktree (`git worktree remove`)
  and deletes its branch (`git branch -d`). A worktree the harness already removed is
  not an error.
- **Fallback.** If the Agent tool in this harness has no `isolation` option, or the first
  spawn with it fails, `flow` says `chains in-session: no worktree isolation` once, and
  runs today's path: one builder per piece, in order, on the feature branch, no merge
  step. The plan's `chain:` letters are then only an ordering hint.
- **Resume (step 0b).** A resumed Deep job also lists `git branch --list` and
  `git worktree list`. A chain branch that exists and is not merged is a chain that was
  started; `flow` says so and finishes with the merge step rather than rebuilding it.
- **Quick and Standard do not change.** One piece, one session.
- **This plan is itself built under the installed plugin**, which is still one builder
  per piece in order. So its pieces run sequentially. The `chain:` letters below show how
  the new template reads, and are not acted on this time.

## Pieces

1. [independent: yes] chain: A — The builder takes a chain and works in a worktree
   File: `agents/builder.md`.
   Frontmatter: add `isolation: worktree`; change `model: opus` to `model: sonnet`; keep
   `effort: high` and the tools list. Body: the three inputs become plan body, chain
   letter, dirty flag. Build the chain's pieces in order through `devflow:build`, commit
   each, stop the chain on the first `stuck: yes`. Report: one `branch:` line, then five
   lines per piece. Add the missing-dependencies rule. Keep every existing rule that
   still applies; "never build a piece other than the one you were given" becomes
   "never build a piece outside your chain". Update the description.
   Verify: python3 skills/test-frontmatter.py
   Done when: `agents/builder.md` frontmatter has `isolation: worktree` and `model: sonnet`;
   its body names the three chain inputs and the `branch:` plus five-lines-per-piece
   report; the frontmatter test passes.

2. [independent: yes] chain: B — The plan template and the chain rules in `flow`
   File: `skills/flow/SKILL.md`, section "Deep only — write the plan down".
   The plan shape gains a `chain:` letter per piece. Add the chain rules: what a chain
   is, at most 4 pieces, two chains never share a file, `chain: final` for shared files,
   list pieces in build order within a chain. Keep the `Done when:` rule.
   Verify: python3 skills/test-frontmatter.py
   Done when: the plan template in `flow` shows `chain:` on each example piece and the
   four chain rules are stated in that section; the frontmatter test passes.

3. [independent: no] chain: B — The loop in `flow`: chains in parallel, merge, cleanup, fallback, resume
   File: `skills/flow/SKILL.md`, sections "Deep — one builder per piece" (rename to
   "Deep — one builder per chain"), step 0b, step 4's Deep line, and Rules.
   The loop: read the plan's chains; spawn one `devflow:builder` per chain with the plan
   body pasted, the chain letter and the dirty flag; at most 4 at once, the rest wait;
   read every report in full, `branch:` then five lines per piece; a report with fewer
   lines than its pieces need, or prose, is `stuck`; on any `stuck: yes` stop spawning
   new chains, let running ones finish, then report. After all chains report: merge
   each chain branch into the feature branch, in plan order, `git merge-tree
   --write-tree` first, then `git merge --no-ff`; a conflict stops and reports. Then
   remove worktrees and branches. Then the `chain: final` chain, if any, alone. Then
   step 5, `submit`. Fallback and resume exactly as the Assumptions say. Rules: replace
   "Never spawn two builders at once" with "Never more than 4 chains at once, never two
   builders on one branch, never resolve a merge conflict yourself".
   Verify: python3 skills/test-frontmatter.py
   Done when: `flow` has a "Deep — one builder per chain" section with the spawn loop,
   the 4-at-once cap, the merge-tree check, the `--no-ff` merge, cleanup, the fallback
   line, and step 0b lists chain branches; the old "one builder at a time, always"
   paragraph is gone; the frontmatter test passes.

4. [independent: yes] chain: C — Docs and README
   Files: `docs/flow.md`, `README.md`, `docs/pipeline.md`.
   `docs/flow.md`: a section "Chains and worktrees" with the why: the 43-minute run,
   why chains not pieces, why a worktree per builder, why merge-tree first, why the
   merge is local and not a PR merge, why 4 at once, why Sonnet (the human's call).
   `README.md`: the loop chart's "Deep: one builder agent per piece, each commits"
   becomes chains in parallel; the size table's Deep row; the skills-table sentence on
   `builder`; drop "Cleanup of worktrees" from "What is not here yet" only if the plan's
   cleanup covers it, otherwise leave it. `docs/pipeline.md`: the sequence diagram's
   "loop one per piece" becomes one per chain in parallel, with a merge step.
   Verify: python3 skills/test-frontmatter.py
   Done when: `docs/flow.md` has the section; `README.md` and `docs/pipeline.md` no longer
   say one builder per piece anywhere; the checks pass.

5. [independent: yes] chain: D — Provenance
   File: `docs/provenance.md`.
   Rows: chains as the unit of parallel work — **Ours**; a worktree per builder —
   **Same idea**, seen in vibe-kanban, Claude Squad, Crystal and ComposioHQ's
   agent-orchestrator, mechanics from Anthropic's Claude Code docs on `isolation: worktree`
   and Workflows; merge-tree before a local `--no-ff` merge — **Ours**; the 4-at-once cap —
   from the field's 4-to-8 working range; Sonnet for the builder — **the human's decision**,
   against the builder-per-piece plan's "evidence first" line, recorded as such. Do not
   name any repo under 1,000 stars. Update the sequential-only row ("Pieces run in order,
   never in parallel") to say it was superseded and when.
   Verify: python3 skills/test-frontmatter.py
   Done when: `docs/provenance.md` has the five rows and the superseded note; no repo under
   1,000 stars is named; `claude plugin validate .` passes with the one expected warning.

6. [independent: yes] chain: E — The Deep eval says chains
   Files: `evals/deep-coordinator/case.yaml`, `evals/README.md`.
   The case's description and expected_outcome say two independent pieces become two
   chains run in parallel, then merged, then submit. Keep every existing grader. Add
   one `tool_used` grader: Bash with `git merge --no-ff`, min 1, weight 2, named
   `merges-the-chains`. `evals/README.md`'s row for the case says what now breaks if it
   fails.
   Verify: python3 evals/test-run.py
   Done when: the case parses, `python3 evals/run.py --dry-run` lists it with the new
   grader, and the eval contract test passes.

## Added after piece 5 reported

Anthropic's worktrees page, read on 2026-09-22, says: "Subagent worktrees use the same
base branch as `--worktree`, so they branch from your repository's default branch unless
`worktree.baseRef` is set to `"head"`." It also says to add `.claude/worktrees/` to
`.gitignore`, that Claude Code holds a `git worktree lock` on a subagent's worktree while
it runs and releases it when the agent finishes, and that a worktree with changes stays on
disk after the agent finishes until a periodic sweep. The Assumption above that the harness
"cuts the branch from the branch `flow` is standing on" is wrong without that setting.

7. [independent: yes] chain: F — Ignore the worktree directory, and tell the builder about the lock
   Files: `.gitignore`, `agents/builder.md`, `docs/flow.md`.
   `.gitignore` gains `.claude/worktrees/`. `agents/builder.md` says its worktree is
   locked by the harness while it runs, so it never runs `git worktree remove` or
   `git worktree prune` itself, and that its branch is named by the harness. `docs/flow.md`'s
   "Chains and worktrees" section gets a short note on the lock, the sweep, and the
   `.gitignore` line, with the docs page named as the source.
   Verify: python3 skills/test-frontmatter.py
   Done when: `.gitignore` contains `.claude/worktrees/`; `agents/builder.md` names the lock
   rule; `docs/flow.md` names the lock, the sweep and the gitignore line; the checks pass.

The human chose, in the second and last question round: **`flow` writes the setting
itself.** The other option, `flow` checks and `setup` offers, was recommended and declined.

8. [independent: no] chain: B — `flow` sets `worktree.baseRef` before the first chain, and proves it took
   Files: `skills/flow/SKILL.md` ("Deep — one builder per chain", before the spawn loop),
   `docs/flow.md`, `docs/provenance.md`.
   Before the first chain spawns: read `worktree.baseRef` from `.claude/settings.local.json`,
   `.claude/settings.json` and `~/.claude/settings.json`. If any of them already says
   `"head"`, print nothing. Otherwise merge `{"worktree": {"baseRef": "head"}}` into
   `.claude/settings.local.json`, creating the file if missing and keeping every key
   already in it, and print exactly one line:
   `settings: wrote worktree.baseRef = head to .claude/settings.local.json — chain worktrees branch from here, and so will your own --worktree sessions`.
   Never write the committed `.claude/settings.json`. If the write fails, fall back to
   sequential and say why in one line.
   Then prove it took, because the setting may be read only at session start: record
   the feature branch's SHA before spawning; when a chain reports its `branch:` line,
   run `git merge-base --is-ancestor <that SHA> <chain branch>`. If it is not an
   ancestor, the worktree was cut from the default branch: do not merge that chain,
   stop the loop, and say `chain <letter> branched from the default branch — the
   setting did not take; restart the session and run flow again to resume`. The chain's
   worktree and branch stay on disk for the human.
   `docs/flow.md`: why the skill writes the setting (the human's call, against the
   recommendation), the side effect on the human's own `--worktree` sessions, and why
   the ancestor check exists. `docs/provenance.md`: one row, **the human's decision**.
   Verify: python3 skills/test-frontmatter.py
   Done when: `flow` has the settings step with the exact printed line, the never-write-
   `settings.json` rule, and the ancestor check with its stop line; `docs/flow.md` and
   `docs/provenance.md` each have the entry; the checks pass.

9. [independent: no] chain: B — The run that writes the setting goes sequential
   Files: `skills/flow/SKILL.md` (the settings step from piece 8), `docs/flow.md`.
   Settings are read when a session starts, so a setting `flow` wrote a moment ago is
   not in force yet. When piece 8's step wrote the file in this run, `flow` does not
   spawn chains: it prints one line, `chains next session: worktree.baseRef was just
   written`, and builds this job on the sequential path, one builder per piece, on the
   feature branch. The ancestor check from piece 8 stays, for the case where the setting
   was already present and still did not take. `docs/flow.md` says why in two sentences.
   Verify: python3 skills/test-frontmatter.py
   Done when: `flow`'s settings step says a write in this run means the sequential path
   and prints that exact line; `docs/flow.md` explains it; the checks pass.
