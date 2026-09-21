# Let a project keep its Deep plans on GitHub instead of in a file

Issue: none

## Why

A plan file is invisible outside the checkout, closes nothing, and is a poor
backlog. An issue is all three. But an issue cannot be read offline or on the
web sandbox, and anyone with write access can edit an order to `build`. So
this is a choice the project makes, not the plugin. Default stays local.

## Assumptions

- The setting is a `## Plans` block in `CLAUDE.md`, like `## Checks`.
  `- Tracker: github` or `- Tracker: local`. No block means local.
- `setup` writes it, and writes it only after proving it: for `github`, it
  runs `gh issue list --limit 1` and must get an answer. Same rule as
  `## Checks`. Never write a tracker you have not reached.
- Local and GitHub only. Linear and Jira stay "paste it" as `flow` says now.
  An adapter each is a plugin of its own.
- A plan issue carries the label `devflow:plan`. Title is the plan name.
  Body is the plan, in the same shape as the file. `setup` creates the
  label if it is missing.
- Step 0b looks for a plan issue only when `Commits ahead` is above 0. A
  fresh Deep job has nothing to resume. This keeps step 0's rule: no
  network on a typo fix.
- `build` does not change. `flow` hands it the piece text, from the file or
  the issue. `build` never reads the tracker.
- On the web, or wherever `gh` is missing, a `github` project falls back to
  local for that run and says so in one line. A plan you cannot read is not
  a reason to stop.
- `submit` adds `Closes #N` for the plan issue. The plan closes on merge.

## Pieces

1. [independent: yes] `setup` asks where plans live and writes `## Plans`
   One question, default local. For github: run `gh issue list --limit 1`,
   and stop with a plain message if it fails. Create the `devflow:plan`
   label if missing. Say the two warnings out loud: no `gh` on the web
   sandbox, and an editable issue is an editable order. Drop the rule
   "never add anything but `## Checks`"; it becomes "only blocks you proved".
   Verify: python3 skills/test-frontmatter.py
   Done when: `setup` on a scratch repo writes `## Plans` with the tracker
   named, and refuses to write `github` when `gh` cannot answer

2. [independent: no] `flow` Deep writes the plan where `## Plans` says
   Local: the file, as now. GitHub: `gh issue create` with the label, the
   title, and the plan as the body. Print the issue number on the size line.
   On failure, fall back to the file and say so.
   Verify: python3 skills/test-frontmatter.py
   Done when: a Deep request on a scratch repo with `Tracker: github` opens
   one labelled issue whose body has the Pieces and Assumptions sections

3. [independent: no] `flow` 0b resumes from a plan issue
   Only when `Commits ahead` is above 0. `gh issue list --label devflow:plan
   --state open`. Match by subject, as the file path does now. Read the body.
   Then the same log read, the same resume line, the same dirty-tree rule.
   Verify: python3 skills/test-frontmatter.py
   Done when: after one committed piece and a `/clear`, `flow` finds the
   issue and announces "resuming ..., pieces 1 built, starting 2"

4. [independent: no] `review` and `submit` know about the plan issue
   `review` step 2: plan issue first, then plan file, then an issue in the
   commits, then nothing. `submit` step 7: `Closes #N` for the plan issue,
   and the PR body links it under What.
   Verify: python3 skills/test-frontmatter.py
   Done when: a PR from a github-tracked Deep job closes the plan issue on
   merge, and `spec-reviewer` quotes lines from the issue body

5. [independent: no] Eval `evals/plans-on-tracker`
   Needs a real GitHub repo, so it cannot scaffold locally. Mark it manual,
   with the steps written out, and keep it out of `run.py`'s default set.
   Verify: python3 evals/test-run.py
   Done when: the case parses and `evals/README.md` explains why it is manual

6. [independent: no] Docs and provenance
   README: two lines under "Set up a project". `docs/flow.md`: one section.
   `docs/web.md`: the fallback. Provenance: one row per assumption above,
   with mattpocock's `setup-matt-pocock-skills` named as the source of the
   local-or-tracker choice.
   Verify: python3 skills/test-frontmatter.py
   Done when: `claude plugin validate .` still prints exactly one warning

## Not in this plan

- Tickets per piece. One issue is the plan. `git log` is the progress.
- A queue, a claim, or a `next` skill. That is unattended work. Later.
- Linear, Jira, Notion. Paste them, as `flow` says.
- Moving `overrides.md` or `CONTEXT.md` to the tracker. Different jobs.
