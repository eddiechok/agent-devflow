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

8. [independent: yes] **The 400-word ceiling stops eating findings silently.** Both agents
   carry a `Not reported:` count, and `review` passes it through. Dropping weak findings
   is the ceiling's job; dropping a Blocking one while printing like a clean review is not.
   Verify: read both agents' return blocks

9. [independent: yes] **`build` commits each plan piece as it lands**, so `git log` answers
   which pieces are built and a plan is resumable for real. `submit` stops short of an
   empty commit when the branch is already committed. It re-opens a decision this branch
   already took — see the note below.
   Verify: read `build`'s commit section; `python3 skills/test-frontmatter.py`

10. [independent: yes] **`tend`** — the skill for a pull request that is already open and
    is telling you something: a red check, a reviewer's comment. Triage first, fix through
    `build`, re-submit through `submit`, which updates the PR.
    Verify: `claude plugin validate .`; read the skill

**Pieces 8, 9 and 10 were added after the fact**, when the three items this plan had put
out of scope were asked for together. Piece 9 in particular reverses a decision taken
earlier on this same branch — the resume promise was deleted rather than built, and is now
built. Recorded rather than tidied away, because a plan quietly rewritten to match the code
is worth less than one that shows where it changed its mind.

## Out of scope

- Reviewing per piece rather than per branch. `review` still runs once, over the whole
  branch, at `submit` time.
- Anything that merges. `ship` is still the only skill that does, and only a human starts it.
