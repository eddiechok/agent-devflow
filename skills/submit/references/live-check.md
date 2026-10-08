# Run the app — the live check

`submit` step 4 reads this whenever there is something to exercise.

Pick whichever of these the project actually is:

- **Something that has to be launched** — a web app, a server, a desktop app. **Use the built-in `run` skill if this environment has it.** If it does not, launch the app the way the project's own README or scripts say to, under the rules below. Do not invent a launcher when the project already documents one.
- **Something you just execute** — a CLI, a script, a one-shot command. **Run it directly**, with the arguments the change affects, and show the output.

**A UI change — any size, Quick included — also gets the browser check.** Read
[browser-check.md](browser-check.md) and follow it: one driver, login once, the exact state the change affects, a desktop and a mobile width, a clean console. It is how you get first-hand proof of a page.

Either way the rule is the same: exercise the change the way a user would, and put the output on screen.

### What counts as proof

**The test is one question: would this have been true before the change?** If yes, it
proves nothing.

- **First-hand** — the thing you are claiming, observed. The response body with the new
  field in it. The page text showing the new label. The CLI's actual stdout for the flag
  you added. A screenshot of the layout you fixed.
- **Second-hand** — true either way. A `200`. A green pipeline. "Server started". An exit
  code. "Tests passed" — step 2 already ran those, and a suite that never covered this
  change passes just as loudly.

**Only first-hand ends this step.** Go and look at the thing itself.

Rules, when you launched something:
- **Put a time limit on it.** If the app never becomes ready, that is a finding to report, not something to sit through.
- **Stop the server when you are done**, unless [a kept server](#a-kept-server) applies. Stop only the process you started. Never kill "whatever is on port 3000" — that may be something the human is running.
- **Screenshots and artifacts go to a temp directory**, never into the repo.

**If it does not work**, either way: fix it and try again, **at most twice**. If it still does not work, print `✗ **live** <what failed>` and **do not open a PR that looks fine**.

Otherwise, once you have looked at the thing itself:

```
✓ **live** POST /settings returns the new field
```

### A kept server

A slow app (several servers, a database, a heavy backend) costs minutes to start, so a project
can ask for its server to stay up. **Keep it only when all three hold**, otherwise stop it as
above:

- `## Workflow` in `CLAUDE.md` has `- Servers: keep`. No `Servers` line, or `- Servers: stop`,
  means stop.
- This is a local session: `[ "$CLAUDE_CODE_REMOTE" = "true" ]` is false. In a cloud session
  the live check always stops its server, because the human's browser cannot reach the
  sandbox's localhost.
- You are not a sweeper. A sweeper always stops its server, whatever the setting.

**Start it detached**, in its own process group, with the log in a temporary directory, never
the repo. The command is the project's own start command, exactly as typed:

```
bash -c 'set -m; nohup sh -c "$1; :" </dev/null >"$2" 2>&1 & echo $!' _ '<command>' '<log>'
```

Under `bash -c`, whatever shell this session runs: zsh refuses `set -m` in a subshell. The
command goes through `sh -c "$1; :"` as an argument: `nohup` alone cannot run an env prefix
such as `PORT=3000 pnpm dev`, and the `; :` keeps `sh` alive, so `ps` shows the whole command. Inside
`'<command>'`, write each `'` of the command as `'\''`, so it stays one argument.

The PID it prints is the server's `pid`. **Never pick a port, never assume one.** Read the
ports the server printed in its log (a lane banner, a "listening on" line) and use those, as
printed. If the ports or lanes are all taken, the server cannot start: stop, name the kept
servers for this repo from the list below with their stop commands, and **never kill them
yourself**. They are the human's.

**Record it.** Append one line to `~/.claude/devflow/servers.tsv`, never in the repo. One line
per kept server, tab-separated, no header: `repo` (the main checkout's absolute path, the
parent of `git rev-parse --path-format=absolute --git-common-dir`), `branch`, `pr` (`-` until
`submit` step 8 knows the number), `ports` (comma-separated, as printed), `pid`, `started`
(ISO 8601) and `command`. Remove the line when the server is stopped or found dead.

**Is it still ours?** Both must hold, or it is not ours: `ps -o pgid= -p <pid>` prints
`<pid>`, and `ps -o command= -p <pid>` contains the whole recorded command. Only
then `kill -TERM -- -<pid>` stops it (the whole group: pnpm, turbo, vite, the backend), and the
line comes off the list. If it is not ours, never kill; take the line off as stale and say so.

**Say it in the PR.** Step 8 adds this section, only when a server was kept. Keep is best
effort, so the start command is always there in case the server died:

```markdown
## Running
- http://localhost:5174 (frontend), http://localhost:9001 (backend)
- PID 4821, started 2026-10-08T14:02 — `pnpm dev`
- Stop it: `kill -TERM -- -4821`
- Not running? Start it again with `pnpm dev`
```
