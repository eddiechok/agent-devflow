# Close the holes the audit found

Branch: `claude/edx-landing-agent-devflow-jw86jc`
Issue: none

**Written before the work, from an audit of every skill.** Seven findings survived,
each with a concrete failing case. One — the plan file's resume promise — is already
fixed and is not repeated here. This plan covers the rest.

## Assumptions

- **The override log prints as well as writes** (piece 6). No answer was given on the
  three options, so the recommendation stands: `flow` keeps writing
  `~/.claude/devflow/overrides.md` and also prints the line, because data silently lost is
  worse than one line of noise.
- **No harness detection anywhere**, same as the web-sessions plan. Every rule is
  written to be true with `gh`, with an MCP server, or with neither.
- **`gh` stays as the worked example** in every skill. Replacing it with prose about
  "GitHub access" everywhere would make the skills vaguer for the common case, which
  is a desktop session that does have `gh`.

## Pieces

1. [independent: yes] **`gh` is not a requirement.** `ship`'s Context line reports a
   missing CLI as "no gh", not as "no PR" — today it says the second, so `ship` tells
   you to submit work that already has an open PR. One line per skill saying the
   commands name what to ask for, not how to ask.
   Verify: read `ship`'s Context block; `python3 skills/test-frontmatter.py`

2. [independent: yes] **`build`'s debug-marker grep** gets the excludes `submit` already
   has, copied verbatim so the two cannot drift again.
   Verify: `grep -n 'exclude-dir' skills/build/SKILL.md skills/submit/SKILL.md`

3. [independent: yes] **`submit` stops asserting the `run` skill exists.** Use it if
   present, otherwise launch the project's own documented way. A Rule generalises it:
   never assert a skill or command exists — check, then fall back. This is the
   `/code-review` lesson, which was fixed once as a special case and never as a rule.
   Verify: read step 4 and the Rules

4. [independent: yes] **`review` finds the plan by listing the directory**, not by
   matching a filename against the branch — the web renames the branch, so the match
   fails on exactly the Deep work that has a spec.
   Verify: read step 2

5. [independent: yes] **`submit` re-derives the danger list from the diff**, rather than
   remembering what `flow` decided. Compaction and a directly-invoked `submit` both
   lose that memory, and losing it silently drops the one security gate.
   Verify: read step 8

6. [independent: yes] **`flow` prints the override line as well as writing it.** The
   file lives in a container that is deleted when a web session ends.
   Verify: read the Recording overrides section

7. [independent: no] **The loop stops being one-way.** `submit` checks for an open PR
   and updates it instead of opening a second; `flow` gains a step 0 that recognises
   follow-up work, reads the PR's Assumptions and the plan before asking anything, and
   still sizes normally so the danger list and the question round survive. Depends on
   piece 1 — "is there an open PR" has to work without `gh`.
   Verify: read `submit` step 7 and `flow` step 0

## Out of scope

- `tend`. Handling CI failures and review comments after the PR opens is still on the
  not-yet list; piece 7 only makes a second `submit` safe.
- Per-piece commits for Deep work. The resume promise was deleted rather than built,
  and building it is a separate decision.
- The 400-word review ceiling not scaling with a five-piece branch. Flagged, not fixed.
