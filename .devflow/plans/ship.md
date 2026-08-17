# ship — merge, deploy, clean up

The tail of the loop. `submit` stops at the open PR, deliberately. Everything
after that is currently typed by hand: in the edx-landing session the message
was literally "create pr, merge, deploy and cleanup".

Two of those five verbs `submit` already does. This covers the other three.

## Assumptions

- **`ship` refuses to run when there is no PR**, and points at `submit` instead.
  Not asked about. Submitting and merging in one uninterrupted command means code
  review, live check, commit, push, merge and deploy all happen without you
  seeing the PR, which is too much to reach in one step. One line, then stop.
- **The merge method follows the repo's existing history** rather than being
  fixed. This repo is linear, so rebase; a repo full of merge commits gets a
  merge commit. Reads `gh repo view` for what is actually permitted.
- **`setup` is not changed.** The `## Deploy` block is optional, and `setup` is
  about check commands. `ship` tells the human to add the block once, in one
  line, the same way `build` does for a missing `## Checks` block.

## Pieces

1. [independent: no] `skills/ship/SKILL.md` — the skill itself.
   The merge gate, the `## Deploy` block and its CI fallback, the live
   verification, and the four cleanups.
   Verify: `python3 skills/test-frontmatter.py` (it picks up new skills
   automatically and will fail on an unquoted description), then
   `claude plugin validate .`

2. [independent: no] `README.md` — the skills table, the loop diagram, "When it
   will ask you", and removing the two "not here yet" entries this closes.
   Verify: read it back; the diagram must still render as mermaid.

## The boundary this must not erode

`submit` promises **"Never merge."** That promise survives only if merging cannot
be reached without a human. So:

- `ship` carries `disable-model-invocation: true`, the same mechanism `setup`
  uses. Checked against the docs rather than assumed: it prevents Claude
  **automatically loading** the skill, keeps it out of subagent preloading, and
  stops a scheduled task firing it. It is not documented as blocking a
  deliberate call by name.
- So the deliberate path is closed the weaker way, by instruction: `flow` and
  `submit` both carry a rule never to call it.
- Worth keeping the two straight. The first draft of this plan claimed the
  frontmatter field made it unreachable, full stop. It does not, and a safety
  claim that is stronger than the mechanism behind it is worse than no claim.

## A lesson to encode, learned the hard way

Merging PR #2 returned `remote: Internal Server Error` and `error: 500` — and
**the merge had already succeeded**. The failure was in the step after it. Left
alone that looks identical to a failed merge, and a blind retry would have been
confusing at best.

So `ship` must check whether a merge landed before reacting to an error from
it: compare the PR state and the remote default branch SHA, not the exit code.

## Not doing yet

- An eval case. The fixture's origin is a bare repo with no GitHub host, so
  `gh pr merge` cannot succeed there and the case would only ever exercise the
  refusal paths. Worth revisiting if the fixture grows a fake forge.
- Anything about `tend` (CI failures, review comments after the PR opens). Still
  a separate, unbuilt skill.

## Renamed after the fact

Built as `land`, renamed before it ever reached main: `land` -> `ship`, and the
old `ship` -> `submit`. The argument against was that `ship` carried weeks of
muscle memory meaning "open a PR and stop", and the rename repoints it at the
irreversible action. Called anyway, deliberately, because "ship" matching
"reaches production" is worth more long-term than one person's habit.

The habit is only half-guarded: no PR on the branch hits the step 1 refusal, a
PR that already exists does not. Written down in the README and in the skill so
the gap is known rather than discovered.
