# The browser check — a UI change

[live-check.md](live-check.md) sends any UI change here, at any size, Quick included. It is
how to get first-hand proof of a page, not a second set of rules: the proof test there still
decides what counts.

## The driver

One driver for the whole check. Mixing two wastes tokens and loses the login.

1. **The project's `## Browser` block.** If the project's CLAUDE.md has one, its `- Driver:`
   line names the driver. Use it when this session has it. `- Driver: session` names none:
   the human chose no preference, so go to 2.
2. **Otherwise the session's own driver.** With no `## Browser` block, or a named driver this
   session lacks, use whatever browser driver the session has.
3. **Say which one you used, by name**, in the live line: `playwright-cli`, `agent-browser`, a
   browser MCP server, the desktop browser pane.
4. **No driver at all.** Say so in one line, and fall back to today's proof: the first-hand
   evidence [live-check.md](live-check.md) asks for, by whatever means the project has. Do not
   install a driver to make the check run.

## The page

Check the real page, on a local server running this branch, before anything else. A page
that needs a login is still the real page: log in as below. A Storybook story is the last
fallback, only when the real page cannot run here, and the live line says you used a story.

## The five checks

Run all five. A page that renders is not a page that is right.

1. **Log in once**, then keep the cookie (a named session or a saved state) so every later
   page reuses it. Take the first of these that works:
   1. A login the driver's browser already has for this app.
   2. The **test credentials** in the project's own files: its CLAUDE.md, its seeds, its
      `.env.example`.
   3. A test login the human gave in chat for this app.
   4. None of these: ask the human once for a test login. No answer → say so, and check
      the pages that need no login.

   Type a test password only on a local server: `localhost`, `127.0.0.1`, `[::1]`, a
   `.localhost` or `.test` name. Never ask the human for a real password, and never type one
   you found anywhere else. Never type a password on a remote site, staging included.
   Never write the password in the PR, the report or a tracked file. Never copy cookies
   from the human's own browser profile into the driver.
2. **Make the exact state the change affects.** Not only the normal page. If the change is the
   empty state, get the list empty. If it is the error message, make the call fail. If it is
   a loading state, hold the request. A change that shows in one state is proven only in that
   state, and the normal page would have looked the same before.
3. **A desktop width and a mobile width.** Look at the change at both, for example 1280 wide
   and 375 wide.
4. **A clean console.** Read the console after the last step. An error or warning the change
   caused is a finding. One that was already there is not yours; note it and move on.
5. **Read only the text that proves the change.** Ask the driver for the one element, label
   or region the change touched. No full-page dumps and no whole accessibility tree in your
   context. Save screenshots to a temp directory and never into the repo, and never read
   one into your context. A layout change is proven by measuring it: ask the driver for the
   element's size, position or computed style at each width.

## Project facts stay in the project

Login, URLs, and traps (a flag the app needs set to show seed data, a port, a slow first
load) belong in the project's CLAUDE.md, not here. Read them there. A fact you had to
discover goes back in as a line for the human to approve, not as a guess in this file.

## The line

Print what you saw, first-hand, and the driver:

```
✓ **live** empty state reads "No orders yet" at 2 widths (playwright-cli)
```

If a check fails, [live-check.md](live-check.md) says what happens next: fix and try again at
most twice.
