---
name: lesson-review
description: "Use to review the lessons the plugin has collected and propose skill changes from them. Started by hand, in a new session, roughly monthly. Reads lessons.md from the private eddiechok/devflow-lessons repo and counts waste from saved sessions, groups by skill and kind, then proposes a change only where the same kind of mistake repeats. Each proposal ships with a new eval case, and a human approves every change before it lands - this skill proposes, it does not edit a skill itself."
argument-hint: ""
---

# lesson-review

Read every lesson. Change a skill only on a repeat, and only with the human's yes.

Why these rules are what they are: [docs/lessons.md](../../docs/lessons.md). Read it only
if a rule looks wrong.

## What this is

`devflow:lesson` only ever collects — one line, appended, nothing more. This skill is the
other half of the loop: it reads what was collected, and turns a pattern into a proposal.

**It proposes; it does not edit a skill itself.** A human approves every skill change, so
the most this skill ever does on its own is write the proposal down and ask.

**Steps 4 to 6 need the agent-devflow checkout.** The eval cases, `evals/run.py` and
`skills/test-frontmatter.py` live there, and the plugin is on in other projects too.
Steps 1 to 3 only read, so they work from any folder. Before step 4, check that
`evals/run.py` and `skills/test-frontmatter.py` exist in this folder. If they do not, print
what steps 1 to 3 found, say this is not the agent-devflow checkout, and stop before step 4.

## 1. Read the lessons

```
gh api repos/eddiechok/devflow-lessons/contents/lessons.md --jq '.content' | base64 -d
```

With no `gh`, use the `add_repo` tool for `eddiechok/devflow-lessons`, then `git clone` it
to a `mktemp -d` dir and read `lessons.md` from there — the same path `devflow:lesson`
falls back to when `gh` is not installed. Remove the temporary directory once you are
done.

## 2. Count waste from saved sessions

```
python3 "<this skill's own directory>/count-waste.py"
```

The plugin install copies this skill's whole directory, so `count-waste.py` sits beside
this file wherever the skill runs. Pass `--since YYYY-MM-DD` to look at only the runs
since the last review, and `--json` if you want the machine-readable form to fold into the
proposals below. The script itself says what it cannot see — "not recorded" rather than a
guess — so pass that straight through rather than smoothing it over.

## 3. Group by skill and kind

Split `lessons.md`'s lines by their `<skill>` and `<kind>` columns, and fold in
`count-waste.py`'s waste numbers under the skill they were charged to. A `mistake` and a
`waste` line about the same skill are still two different kinds, and stay apart.

## 4. Propose, following the rules

Four rules govern every proposal, from `docs/lessons.md`:

- **Only repeats.** A skill changes only when the same kind of mistake shows up at least twice.
  One mistake is a note, not a pattern — leave it in the file, unproposed. A line
  with no repeat after about 30 days leaves the review and moves to `archive.md` in the
  lessons repo, so nothing is lost, just no longer live.
- **A size budget.** Every proposal states its net line change in words, and deletes as
  well as adds where it can. It must not push the skill over its cap — 500 lines, except
  `flow` at 1059 and `ship` at 535 (`skills/test-frontmatter.py` enforces this). More text
  is not better.
- **A rule becomes a check.** A lesson that is really "never do X" becomes a hook or a
  script check, like the ones in `hooks/`, not another sentence in a skill. A sentence can
  be ignored; a check cannot.
- **Waste and ideas prove it in numbers.** A change with no mistake behind it — a `waste`
  or `idea` lesson — must show, from `count-waste.py`'s own numbers, that it is faster,
  cheaper, or needs fewer prompts, with the evals unchanged. No numbers, no proposal.

Each proposal comes with a new eval case under `evals/`, built the same way the existing
cases under `evals/` are, so the pattern this lesson caught has a test that stays.

## 5. Check old against new

**Running the evals themselves costs money.** Ask the human before running `python3 evals/run.py`,
once, for this batch of proposals — it drives real Claude sessions, and it never runs unasked.

With the yes: run the whole eval suite on the skill as it is today, then again on the
proposed version, including the new case. A change that makes any existing case worse does
not go in, even when the new case passes. Report both runs side by side.

## 6. Hand it to the human

For each proposal: the lesson lines behind it, the skill change (a diff, not a rewrite),
its net line count, the new eval case, and the old-against-new result. **A human approves
every skill change** — this skill never applies one on its own, whatever the evals say.

On a yes, apply that one proposal exactly as shown, then re-run `skills/test-frontmatter.py`
and `claude plugin validate .` before calling it done.

## Output

Every line a human reads takes one shape: a mark, a bold one-word lowercase label, then
the result — for example `✓ **checks** 3 of 3 pass, exit 0`.

- `✓` done. `✗` failed or stopped. `–` (en dash) skipped, or nothing to do.
- `→` next: planned, or waiting on you.
- One line per step, each standing alone with a blank line before and after it.
- Keep each line to 80 characters — detail goes on the next line, or in the PR.

## Rules

- Never edit a skill without a human's yes on that specific proposal.
- Never propose a change for a mistake that has not repeated, unless it is moving an
  unrepeated one to `archive.md` after about 30 days.
- Never run `python3 evals/run.py` without asking the human first — it costs real money.
- Never propose a change that pushes a skill over its size budget.
- Never turn a "never do X" lesson into skill prose when it can be a check instead.
- Never let a waste or idea proposal through without numbers proving it is faster,
  cheaper, or needs fewer prompts.
