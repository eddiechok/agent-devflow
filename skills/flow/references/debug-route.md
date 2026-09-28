# A bug nobody can point at goes to `debug`, not `plan`

A bug you can already point at — the file, the function, the line — has nowhere left to go
but `build`, on `build`'s own test-first loop, exactly as any other Quick or Standard change
does. Nothing here changes for that bug.

**A bug nobody can point at is different, and it is easy to misread as Deep.** Deep's own
test is "you cannot name the files it touches yet" — true of this bug too, which is why it
needs a rule of its own rather than falling through to Step 2's table. Not knowing where a
*feature* belongs is a design question, and `plan` exists to answer it across many files and
several pieces. Not knowing where a *bug* is is a different question with a different
answer: one command that makes it show itself. That is `devflow:debug`'s job, not `plan`'s,
and it stays a single piece of work — sized Standard, never Deep, whatever the sizing table's
Deep row seems to say about the files.

## Recognising the case

The request describes broken behaviour — wrong output, an error, a crash — and nothing in
it, the issue, or this session's own reading of the code, names a specific file, function or
line the bug lives in. A stack trace, a failing test already in the repo, or a hunch checked
and confirmed all count as "can point at it" and skip `debug` entirely. A guess that has not
been checked does not count.

## Calling `devflow:debug`

Call it with the request as `debug` received it — the bug in the human's own words — and
whatever has already been tried, if the request or the issue says. `debug` builds a
red-capable loop, reproduces and shrinks the bug, ranks causes, and reports back exactly two
things: **the cause**, and **the red command** that proves it.

**If `debug` stops instead of reporting** — it could not build a loop at all — it is asking
the human for a log, access, or a way to reproduce the bug. Relay that question and stop.
Do not call `build` on a guess.

## Handing the report to `build`

Call `devflow:build` with `debug`'s cause and red command as the piece to build: the red
command becomes `build`'s first failing test, already proven red, and `build` writes the fix
that turns it green, through its usual five gates. Then call `devflow:submit`, the same
Standard path as any other change — `debug` only changed how the piece was found, not what
happens once it is.
