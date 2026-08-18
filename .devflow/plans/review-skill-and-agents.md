# A review that can actually run

Branch: `feat/review-skill-and-agents`
Issue: none

**Written after the work, from the requests that drove it — not from the diff.** Said plainly because it matters when reading it: a plan reverse-engineered from finished code cannot disagree with that code, the same way a test that recomputes the answer the way the code does cannot disagree with it. The pieces below are what was asked for, in the order it was asked, so the spec axis has something independent to judge against.

## Why

`submit` step 5 told the model to run the built-in `/code-review` and asserted "It is already installed". It could not run: the plugin is not installed here, it is a slash command a skill cannot type at itself, and it reviews an **open pull request** — four steps before `submit` has one. The instruction sat there looking like a review had happened.

## Assumptions

- Agents rather than prompt templates, so the limits are enforced by `tools:` rather than asked for in prose. Both libraries that solve this use templates plus a general agent; one of them documents a fan-out bug that a restricted agent cannot have.
- `/code-review` is kept and moved rather than replaced. It is the better review; it just needs a PR to read.
- The second axis runs only when a spec exists, so a Quick fix costs what it did before.

## Pieces

1. [independent: no] A `review` skill: pin the fixed point, prove it resolves before spawning, find the plan or issue, spawn the axes, report both without blending them.
   Verify: `python3 skills/test-frontmatter.py`

2. [independent: no] A `reviewer` agent — is it built right. Reads the branch including untracked files. Reports only what it can attach a named failing input to.
   Verify: `python3 skills/test-frontmatter.py`

3. [independent: no] A `spec-reviewer` agent — is it the right thing. Missing requirements, requirements built wrong, and behaviour nobody asked for. Every finding quotes a line of the spec.
   Verify: `python3 skills/test-frontmatter.py`

4. [independent: no] `submit` step 5 calls `review` instead of reviewing inline, and a finding may be rejected — but only checked, in writing, and visible in the PR.
   Verify: read the step; no check covers prose

5. [independent: no] `submit` step 8 hands `/code-review` and `/security-review` to the human, with the PR number, and never claims either ran.
   Verify: read the step

6. [independent: yes] The frontmatter test covers `agents/*.md` under the same contract as skills.
   Verify: `python3 skills/test-frontmatter.py`

7. [independent: yes] A provenance doc: where every step in devflow came from and why, in plain English, labelled by how strong the link is. Kept out of the `SKILL.md` files, which are prompts.
   Verify: read `docs/provenance.md`

8. [independent: yes] `build` rejects a test that computes its expected value the way the code does, and names the tell for testing internals.
   Verify: `python3 skills/test-frontmatter.py`

9. [independent: yes] `submit` step 3's debug-marker grep stops failing on documentation.
   Verify: `grep -rn "\[DBG-" . --exclude-dir=node_modules --exclude-dir=.git --exclude='*.md'` returns nothing

## Out of scope

- The `hardcase` agent — a second, adversarial read. Still on the not-yet list.
- Filling in provenance for steps whose sources cannot be established from the files.
- Anything that merges.
