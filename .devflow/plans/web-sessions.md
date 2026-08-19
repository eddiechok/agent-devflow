# Make devflow survive a web session

Branch: `claude/edx-landing-agent-devflow-jw86jc`
Issue: none

**Written before the work, from an audit of a real session.** The edx-landing session
`session_019Vw…` ran the copy-reduction change on 18 Aug with the plugin installed,
enabled and visible, and used none of it. Asked afterwards what it ran, it answered:
zero Skill calls, no review, no live check, no PR, and a commit type it invented.

That session was not being careless. Three of devflow's steps are **forbidden by the
harness** in Claude Code on the web, and devflow says nothing about any of them, so the
model met a wall with no instruction and walked around it.

## Why

The web harness adds instructions of its own to the system prompt. Three of them
collide with devflow:

| Harness says | devflow step it blocks |
|---|---|
| "Do not call the AgentTool unless the user requested it" | `review` step 3 — both axes are agents |
| "Do NOT create a pull request unless the user explicitly asks for one" | `submit` step 7 — the PR is the whole point |
| Develop on this branch, "NEVER push to a different branch" | `build`'s `git checkout -b <type>/<short-name>` |

The first is the dangerous one. A blocked review is silent: the axes never start, nothing
prints, and `submit` carries on to a PR that reads as reviewed. That is the exact failure
the `/code-review` fix was written for, arriving through a different door.

## Assumptions

- **Invoking `submit` is the explicit request for a PR.** Its own description says it
  opens one, and so does `flow`'s. A human who typed the command has asked. Taken as a
  recommendation, not checked with anyone.
- **The review block is real and only the human can lift it.** So `review` asks once and
  reports `NOT RUN` if no answer comes. It does not review inline instead — a session
  reviewing its own code is what the two agents exist to avoid.
- **The branch conflict is already handled** and needs a line of text, not a fix: `build`
  only creates a branch when HEAD is the default branch, so a handed branch is left alone
  today. The line stops a future reading that renames it.
- No harness detection. Nothing here checks which harness it is in — every rule is written
  to be correct in both.

## Pieces

1. [independent: yes] `review` step 3 names the block, asks once in one line, and step 4
   gains a `NOT RUN` state. A rule says `NOT RUN` and `none` are different answers.
   Verify: `python3 skills/test-frontmatter.py`

2. [independent: no] `submit` step 5 treats `NOT RUN` as an unresolved finding — into
   **Known issues**, and **Evidence** says which axes ran. Depends on piece 1 for the word.
   Verify: read the step

3. [independent: yes] `submit` step 7 states that invoking the skill is the request for the
   PR, and gives the fallback when the environment blocks it anyway: push, then hand over
   the compare link and the `gh` command. Never end silent on a pushed branch.
   Verify: read the step

4. [independent: yes] `submit` step 1 and `build`'s branch step: a branch you were handed
   is a branch. Keep it, do not rename it to fit the convention.
   Verify: `python3 skills/test-frontmatter.py`

5. [independent: yes] `README.md` gains a web section: the three effects, and the one thing
   the plugin cannot fix — on the web you have to type `/devflow:flow` yourself, because
   the harness has already told the model to implement, commit and push.
   Verify: read `README.md`

6. [independent: yes] `docs/provenance.md` records all of it as **Real bug**, against the
   session that found it.
   Verify: read `docs/provenance.md`

## Out of scope

- Making `flow` fire by itself on the web. A skill's description cannot outrank the task
  description the harness wrote. Documented instead.
- Anything that detects the harness at runtime.
- The exit codes the audited session lost to `| tail`. `build` and `submit` already say to
  run checks bare; that session ran no skill, so no rule of ours was in play.
