# setup, in detail

Why `setup`'s steps are what they are. The steps themselves are in
[the skill](../skills/setup/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/setup/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

## Why this matters

Everything downstream trusts the `## Checks` block. `build` runs it after every change, `submit` runs it fresh before opening a PR, and the output hook keys off it.

A wrong or stale command here fails **silently**: `submit` runs something harmless, sees exit 0, and reports the work as proven. That is the worst kind of failure in this plugin, so nothing gets written to `CLAUDE.md` until it has actually been run.

## Step 3 — running each command

This is the point of the skill.

### Running them bare

The bash hook trims
the output and prints `exit=N` itself, which is the pass/fail signal you need
here — but only for a plain command. Shape it yourself and the hook steps aside,
and you are back to reading a wall of output and guessing the exit code.

This matters more here than anywhere: a command you cannot read the exit code of
is a command you have not really proven, and proving them is the whole job.

## Step 4 — writing the block

Two honest lines beat one invented wrapper script.

## Step 5 — where plans live

No block means local, and that is the safe outcome without a claim the human did not make.

The second label, `devflow:backlog`, is made alongside `devflow:plan` for the same reason: `flow` needs it the first time a request names more than one feature, and asking for it there would cost a round trip this step can pay for once, up front. A project on `local` gets no label, but `flow` still has somewhere to park the rest — a file under `.devflow/backlog/`.
