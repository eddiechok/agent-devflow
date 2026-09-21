# The bash hook

What `hooks/bash-guard.py` does, why each part is there, and what it costs you. The short version is in the [README](../README.md).


`hooks/bash-guard.py` does three things. All are cheap, and all are worth knowing about.

**Trims long check output.** A 500-line test run becomes about 40 lines.

On failure it shows **more**, not less. You get the matching failure lines plus the last
40. A failing command is exactly when you want detail. The exit code is always printed as
`exit=N`.

**Allows the commands it trims.** It has to.

Claude Code checks permissions against the command the hook hands back, not the one Claude
typed. And no `Bash(...)` rule can match a compound statement.

Without this, every permission rule refuses `npm test`, however you write them. Claude does not stop
there. It quietly runs `node --test` instead, going around the command your `## Checks`
block named. So the hook carries the decision itself.

Only a single, simple call to a known check runner ever gets that far. The command must
match the built-in list: `npm test`, `pytest`, `cargo test`, `go test`, `tsc`, and
friends. It must contain no `&&`, `||`, `;`, `|`, newline, `$(` or backtick. Anything else
passes through untouched, and faces your normal rules.

This is why `build` and `submit` both insist on running check commands **bare**, one per
call.

A command Claude has already shaped makes the hook stand down. `npm test 2>&1 | tail -20`
is one. You lose the trimming and the `exit=N` line. Claude then works out an exit code by
hand instead. It gets that wrong: `${PIPESTATUS[0]}` after a `;` printed nothing at all in
a real run.

**Asks before committing to the default branch.** It asks rather than blocks. A wrong ask
costs one keypress. A wrong block stops your work.

> ⚠️ **This stops mistakes. It does not stop attackers.** It matches text in
> command strings. Variable indirection, aliases, or a different binary get past it
> easily. It stops accidents, not attackers. It also fails open. Any error and your
> command runs unchanged.
>
> **Note which way the trimming grant points.** For that narrow set of commands the hook
> *gives* permission rather than withholding it. A hook allow beats your own settings. A
> `"deny": ["Bash(npm:*)"]` entry does **not** stop it. That was tested, not assumed.
> `npm test` runs whatever `package.json` says. So this is a real grant, even if a small
> one. If you would rather keep that decision, drop the `PreToolUse` entry from
> `hooks/hooks.json`. You lose the trimming and get the prompts back.
