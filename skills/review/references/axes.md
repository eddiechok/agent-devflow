# Spawn the axes

`review` step 3 reads this, on every run without a `no-behaviour:` line.

Both get the fixed point, the file list, and a **400 word ceiling**. Both run in parallel where you can, and neither is told what the other found.

- **`devflow:reviewer`** — always. Is it built right.
- **`devflow:spec-reviewer`** — only when step 2 found a spec. Is it the right thing. Pass it the spec's path or contents.

Do not paste this session's reasoning, your plan, or your own account of what the change does into either prompt — that is the thing an independent reviewer would not have. Give them the range and let them read it.

### Then start `security-reviewer`, if the danger list says so

`reviewer`'s `## Danger list` line names what the change touched. Start
`devflow:security-reviewer` only when that line names one of five items:
auth and permissions, secrets and keys, payments, public API or wire format,
CI/CD config. The other three items on the same list — database migrations,
deleting or weakening tests, anything that cannot be reverted — do not start it.

Give it the same fixed point and file list as the other axes, and the same 400 word
ceiling. It does not read `reviewer`'s report; it reads the change itself, as an attacker.

No security item named → print `– **review** no security item touched — security-reviewer skipped` and go on.

### Then the project's own review agents

Read the `## Workflow` block of `CLAUDE.md` for `- Review agent: <name>` lines, one agent
each. `devflow:skills` writes them, after the human said yes to that agent. Start each
named agent with the same fixed point, file list and 400 word ceiling as the other axes,
in parallel with them, and nothing else. No line → no project axis: print nothing, and
leave it out of the report.

**Run only what a line names.** Never look in `.claude/agents/` for others: an agent nobody
chose may edit files or call the network, and the line is the human's choice, in writing.

A name that will not start — no agent by that name — is `NOT RUN — no agent named <name>`
under **Project review**, with `✗ **review** <name> did not start — Project review NOT RUN`.
Its report is in the project's own shape. Print it as the agent wrote it.

Each project agent's findings go to `hardcase` too, below, under the agent's name. A project
agent's finding that falls writes no lesson: the agent is the project's, not devflow's.

### Then challenge the first axis, and the security axis

**`devflow:hardcase`** — a third agent, and the only one that runs after the others,
because it needs something to argue with. Give it the fixed point, `reviewer`'s findings,
and `security-reviewer`'s findings when it ran, and each project agent's findings under its
name, and nothing else: not the spec, not `spec-reviewer`'s report, and not this session.

**Only when `reviewer`, `security-reviewer` or a project agent reported something.**
All clean has nothing to refute, so print `– **review** clean — nothing to challenge` and skip it.

**It challenges `reviewer`, `security-reviewer` and the project agents, never
`spec-reviewer`.**

It does not get a vote. It reports which findings stand, which fall and why, and `submit`
decides.

## In the step 4 report

**`Challenged` sits under `Built right` because it is about that axis, not beside it.**
It is not a third axis and it never appears in `Worst of each` — there is no worst
challenge. `Security` is different: `security-reviewer` finds things the other axes are
not shaped to see, so it ranks in `Worst of each` beside `Built right` and `Right thing`.
Print `hardcase`'s three sections as it wrote them, `Falls` first, and do not delete a
finding from `Built right`, `Security` or `Project review` because it fell.

**`Project review` is one section for every named agent**, each report under `### <name>`.
It ranks in `Worst of each` like `Security`, with one `Project review:` line: the one finding
that matters most across those agents, or none.

**Each finding under `Falls` writes a lesson.** Call `devflow:lesson` — skill is whichever
agent raised it, `reviewer` or `security-reviewer`, kind `mistake`, what `<agent> flagged
<the finding, short>; hardcase refuted it`, proof the branch's HEAD commit or the PR. Still
print both sections as `hardcase` wrote them; this is in addition to that, not instead.
