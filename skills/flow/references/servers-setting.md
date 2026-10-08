# Ask the Servers question once, and name the leftovers

`flow` reads this after step 0c, before step 1, when its `Servers` Context line says `none`
and names start hints, or its `Kept servers` line names a server. `submit`'s live check can
leave its dev server up for a slow app ([live-check.md](../../submit/references/live-check.md#a-kept-server)),
and reads `- Servers: keep` or `- Servers: stop` from `## Workflow` to know. Setup's step 6b
writes that line, but setup's step 1 sends a project that already has `## Workflow` past
step 6, so a project set up before step 6b existed never got the question. This asks it here.
The same read also finds the servers an earlier run left up.

**What the Context lines cost.** Both run when the skill loads, so they take no turn. `Servers`
reads `CLAUDE.md` and a few file names. `Kept servers` reads one local file,
`~/.claude/devflow/servers.tsv`, and calls GitHub (one REST call per kept server of this repo)
only when that file has a line for this repo. With none, the model sees one short line,
`Kept servers: none`, and this file is never read. The list is never fetched from GitHub.

## The question

**Ask after step 0c; write at step 5**, for the reason [browser-driver.md](browser-driver.md)
gives: asked earlier, the answer would dirty a folder step 0c reads as clean, and written
before `build` cuts its branch it stops the cut. So **hold the answer** and write the
`- Servers:` line into the `## Workflow` block at step 5, after `build` or the last builder
hands back and before `submit`, which commits it on the job's branch.

1. **Only a repo whose live check starts a server gets the question.** For a library, a CLI or
   a one-shot script → print nothing and go on. The hints are a first look; confirm them by what
   the project's README or scripts start, the same read as setup's step 6b.
2. **If setup ran this run**, its step 6b already asked. Do not ask twice.
3. **Otherwise** → follow [setup's step 6b](../../setup/SKILL.md#6b-keep-the-dev-server-running)
   alone: its question and its recommendation, exactly as it says, and none of setup's other
   steps. Print its `servers` line, then go on. Its line waits for step 5.

Every answer writes the line, so the question comes once per project. A run that **stops before
step 5** never wrote the held answer and asks again next run. The question is never asked in
`submit`: a run that stops at its end waits on someone who has gone. A Quick run asks it too,
because it is a question about the project, not about the work.

## Leftovers

Each `Kept servers` entry shows its branch, PR number, PR state, PID, ports and start command.
**A leftover is a kept server whose PR is merged or closed.** An open PR, a PR not opened yet
(`no PR yet`) or a state that could not be read is somebody's work in progress: say nothing.

For each leftover, name it with its stop command and offer to stop it, in one popup (or one line
where there is none):

```
→ **servers** kept for #12 (merged): ports 5174,9001, PID 4821, `pnpm dev`
  Stop it? (kill -TERM -- -4821)
```

Stop one only on the human's yes. Never stop one without the human's yes, and a no leaves the line in the list.
On a yes, stop it by the same check `ship` uses. It is ours only when both hold, or it is not
ours: `ps -o pgid= -p <pid>` prints `<pid>`, and `ps -o command= -p <pid>` contains the whole recorded command. Ours → `kill -TERM -- -<pid>`, which stops the whole group, then take the
line off `~/.claude/devflow/servers.tsv`. Not ours → never kill; the PID was reused or the server
died, so take the line off as stale and say so. Never stop anything else.

The offer comes once, before step 1, and does not hold the request: after the answer, go on.
