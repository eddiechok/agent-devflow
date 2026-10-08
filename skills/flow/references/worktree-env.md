# Ask about env files once

`flow` reads this after step 0c, before step 1, when its `Env files` Context line says `none`
and names env files. A gitignored `.env` never reaches a new worktree, and a `.worktreeinclude`
at the repo root makes Claude Code copy it into every one it makes. Setup's step 6c writes that
file, but setup's step 1 sends a project that already has `## Workflow` past step 6, so a
project set up before step 6c existed never got the question. This asks it here.

**Why the Context line.** It runs when the skill loads, so it costs no turn. It looks in the
main checkout, not in this folder: in a worktree, the env files are the very thing missing.
It prints paths only and never opens a file. A repo with no ignored env files, or with a
`.worktreeinclude` already, never reads this file.

**Ask after step 0c; write at step 5**, for the reason [browser-driver.md](browser-driver.md)
gives: asked earlier, the file would dirty a folder step 0c reads as clean. So **hold the
answer** and write `.worktreeinclude` at step 5, after `build` or the last builder hands back
and before `submit`, which commits it on the job's branch.

1. **If setup ran this run**, its step 6c already asked. Do not ask twice.
2. **Otherwise** → follow [setup's step 6c](../../setup/SKILL.md#6c-env-files-in-every-worktree)
   alone: its read, its question and the file it writes, exactly as it says, and none of
   setup's other steps. Print its `env` line, then go on to step 1. Its file waits for step 5.

Every answer writes the file, "Never copy" included, so the question comes once per project.
A run that **stops before step 5** never wrote the held answer and asks again next run. The
question is never asked in `submit`: a run that stops at its end waits on someone who has
gone. A Quick run asks it too, because it is a question about the project, not about the work.
