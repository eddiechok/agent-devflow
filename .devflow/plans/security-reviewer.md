# Security reviewer: an attacker's-eye review agent, replacing the manual /security-review offer

Issue: none — request typed in chat, 2026-09-24

## Why

`reviewer` flags when a change touches the danger list, then hands the security
question to a human, who is offered `/code-review` and `/security-review` at the end
of `submit`. `/code-review` repeats the review devflow already ran. `/security-review`
is the one check nobody runs by default. A fresh agent that reviews as an attacker —
only on changes that touch the security items of the danger list — closes that gap,
works in every harness, and lets the `opinion` line go.

## Assumptions
- PR #40 merges first; this work is cut from the `main` that has it (both touch
  skills/submit/SKILL.md and skills/test-frontmatter.py).
- `hardcase` challenges `security-reviewer`'s findings too — the source repo runs a
  false-positive filter per finding, and hardcase is that job.
- The trigger is the security subset of the danger list only: auth and permissions,
  secrets and keys, payments, public API or wire format, CI/CD config. Deleted tests,
  migrations and irreversible changes do not start it.
- `reviewer` keeps reporting any attacker finding it happens to see, because
  `security-reviewer` does not run on every change. A finding both report is fixed once.
- Checklist source: anthropics/claude-code-security-review (6,262 stars, MIT),
  `.claude/commands/security-review.md` — its categories, its exploit-only bar, its hard
  exclusions and precedents. Read on 2026-09-24. Credited in docs/provenance.md.
- Model and effort match `reviewer`: opus, xhigh. Report shape mirrors `reviewer`'s.

## Pieces
1. [independent: no] chain: A — Add the security-reviewer agent
   agents/security-reviewer.md: read-only (Read, Grep, Glob, Bash), fresh context,
   reviews the change between a fixed point and now as an attacker would. Reports only
   findings with a concrete exploit case (who, what input, what they get). Categories,
   bar, exclusions and precedents adapted from the source prompt, which is at
   https://github.com/anthropics/claude-code-security-review/blob/main/.claude/commands/security-review.md
   — read it with `gh api repos/anthropics/claude-code-security-review/contents/.claude/commands/security-review.md --jq .content`
   and base64-decode it before writing a line. Under 400 words, sections
   `## Exploitable`, `## Reviewed`, and a `Not reported:` line when the limit bit.
   Credit the source in docs/provenance.md with its star count.
   Verify: python3 skills/test-frontmatter.py
   Done when: the agent parses with a model and effort, its report sections and
   exploit bar are pinned, and provenance names the source repo.
2. [independent: no] chain: A — review starts it on security danger-list touches
   skills/review/SKILL.md: after `reviewer` returns, start `security-reviewer` only when
   its Danger list line names a security item; `hardcase` challenges its findings as
   well as reviewer's; the step 4 report gets a `## Security` section (or `skipped — no
   security item touched`, or `NOT RUN — <why>`) and a Security line in Worst of each.
   agents/reviewer.md: the danger-list line names which item, because it now decides
   whether security-reviewer runs. agents/hardcase.md: accepts security findings.
   docs/review.md: the agent table and the reasons.
   Verify: python3 skills/test-frontmatter.py
   Done when: the spawn condition, the security item list, the hardcase scope and the
   new report section are pinned.
3. [independent: no] chain: A — submit fixes security findings and drops the opinion line
   skills/submit/SKILL.md: step 5 treats Exploitable findings like Blocking (fix, 2
   rounds, round 2 scoped to security-reviewer, Known issues after that); NOT RUN and
   skipped are named in Evidence; step 9 no longer offers /code-review or
   /security-review, and the re-derive-the-danger-list paragraph goes with it.
   docs/submit.md and docs/provenance.md row 9 updated to match. The `→ **opinion**`
   pin in skills/test-frontmatter.py is replaced by a pin that it is gone.
   Verify: python3 skills/test-frontmatter.py
   Done when: no skill prints an opinion line, and submit's handling of security
   findings is pinned.
4. [independent: no] chain: A — README and flow say the agent runs the security review
   README.md: the danger-list and agents sections name security-reviewer instead of a
   manual /security-review. skills/flow/SKILL.md step 2: the danger list line says the
   review will include security-reviewer, not that a human should run one.
   Verify: python3 skills/test-frontmatter.py
   Done when: nothing in README.md or skills/ tells the human to run /security-review.
