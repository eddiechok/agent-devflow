# devflow

The words this project uses, and what each one means here. `build` reads this file and
never writes it.

## Words

**direct** — commit straight on main, no branch, no pull request. It names the way the work
is done, not how many people work on the project: a team can work direct, and one person can
work in `pr`. A project picks it in `## Workflow` in its `CLAUDE.md`, as `Mode: direct`.

**pr** — a branch and a pull request for each job. The way `devflow` worked before `direct`
existed, and still the way when `CLAUDE.md` says `Mode: pr`, or when one run says `--pr`.
