# The browser check — a UI change

[live-check.md](live-check.md) sends any UI change here, at any size, Quick included. It is
how to get first-hand proof of a page, not a second set of rules: the proof test there still
decides what counts.

## The driver

One driver for the whole check. Mixing two wastes tokens and loses the login.

1. **The project's `## Browser` block.** If the project's CLAUDE.md has one, its `- Driver:`
   line names the driver. Use it when this session has it.
2. **Otherwise the session's own driver.** With no `## Browser` block, or a named driver this
   session lacks, use whatever browser driver the session has.
3. **Say which one you used, by name**, in the live line: `playwright-cli`, `agent-browser`, a
   browser MCP server, the desktop browser pane.
4. **No driver at all.** Say so in one line, and fall back to today's proof: the first-hand
   evidence [live-check.md](live-check.md) asks for, by whatever means the project has. Do not
   install a driver to make the check run.

## The five checks

Run all five. A page that renders is not a page that is right.

1. **Log in once.** Use the project's seeded user, then keep the cookie (a named session or a
   saved state) so every later page reuses it. Use **test credentials from the project's own
   files** only: its CLAUDE.md, its seeds, its `.env.example`. Never ask the human for a real
   password, and never type one you found anywhere else. No test login in the project's files
   → say so, and check the pages that need no login.
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
   context. Save screenshots to a temp directory and never into the repo; never read a
   screenshot into context unless you are reading that one image to judge the layout.

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
