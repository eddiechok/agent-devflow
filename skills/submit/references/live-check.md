# Run the app — the live check

`submit` step 4 reads this whenever there is something to exercise.

Pick whichever of these the project actually is:

- **Something that has to be launched** — a web app, a server, a desktop app. **Use the built-in `run` skill if this environment has it.** If it does not, launch the app the way the project's own README or scripts say to, under the rules below. Do not invent a launcher when the project already documents one.
- **Something you just execute** — a CLI, a script, a one-shot command. **Run it directly**, with the arguments the change affects, and show the output.

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
- **Stop the server when you are done.** Stop only the process you started. Never kill "whatever is on port 3000" — that may be something the human is running.
- **Screenshots and artifacts go to a temp directory**, never into the repo.

**If it does not work**, either way: fix it and try again, **at most twice**. If it still does not work, print `✗ **live** <what failed>` and **do not open a PR that looks fine**.

Otherwise, once you have looked at the thing itself:

```
✓ **live** POST /settings returns the new field
```
