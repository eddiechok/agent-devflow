# Ask the browser driver once

`flow` reads this after step 0c, before step 1, when its `Browser block` Context line says
`none` and names UI hints. `submit` checks a UI change in a browser with the driver a
`## Browser` block names ([browser-check.md](../../submit/references/browser-check.md)), and
setup's step 6a writes it. But setup's step 1 sends a project that already has `## Workflow`
past step 6, so a project set up before step 6a existed never got the question. This asks it
here.

**Ask after step 0c; write at step 5.** By step 0c's end the run stands in the folder its work
lands in. Asked before, the answer would dirty a folder step 0c reads as clean, and stay behind
when step 0c moves the run to a worktree. Written before `build` cuts its branch, it stops the
cut: `git checkout -b <name> <default branch ref>` refuses a changed `CLAUDE.md` that differs
there. So **hold the answer** and write the block at step 5, after `build` or the last builder
hands back and before `submit`, which commits it on the job's branch.

**Why the Context line.** It looks for the block and for UI files when the skill loads, which
costs no turn. A repo with no UI hints never reads this file, so it pays nothing on any run.

1. **No UI** → print nothing and go on to step 1. The hints are a first look; confirm them the
   same way as [the skills skill's step 3a](../../skills/SKILL.md#3a-a-repo-with-a-ui).
2. **If setup ran this run**, its step 6a already asked. Do not ask twice; go on to step 1.
3. **Otherwise** → follow [setup's step 6a](../../setup/SKILL.md#6a-a-browser-driver-in-a-ui-repo)
   alone: its question and its proof, exactly as it says, and none of setup's other steps. Print
   its `browser` line, then go on to step 1 with the request. Its block waits for step 5.

Every answer writes the block, "Use whatever the session has" included, so the question comes
once per project. Two exceptions ask again on the next run: a driver that is **not installed**,
since step 6a writes no block for it; and a run that **stops before step 5** (a red build, or
the human saying not to submit), since the held answer was never written. Both cost one
repeated question, and nothing else.

The question is asked here, at the start of the run, while the human is at the keyboard. It is
never asked in `submit`: a run that stops at its end waits on someone who has gone. A Quick run
asks it too, because it is a question about the project, not about the work.
