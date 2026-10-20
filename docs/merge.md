# merge, in detail

Why `merge`'s steps are what they are. The steps themselves are in
[the skill](../skills/merge/SKILL.md), and the short version is in the
[README](../README.md).

## Why it exists

`ship` merges, deploys, live-checks and cleans up in one command. A `Deploy:` line deploys
the main checkout at the merged commit, so one deploy ships every PR merged before it. A
human with three PRs ready used to run `ship` three times and deploy three times.
`/devflow:merge` is the merge half alone: merge each PR, then run `/devflow:ship` once.

## Why it reads ship instead of copying it

The refusals, the merge method ladder, the conflict handover and the branch clean-up took
many runs to get right. A second copy would drift. So `merge` points at `ship`'s steps 1, 2,
3 and 6 and says only what differs: no deploy, no live check, its own report.

## Why it reads the Deploy block first

Whether a merge starts a deploy depends on the project, and the `## Deploy` block is where
the project says so. It is read before ship's step 1, because step 2 can hand a conflicting
PR to `tend`, which pushes to its branch. A refusal that came after that would leave a
branch rewritten for a merge that was never going to happen.

- **No `Deploy:` line** means CI deploys when the default branch moves. A merge here starts
  the deploy, so `merge` would defeat its own purpose. It stops and merges nothing, and
  names `/devflow:ship <n> <n>` for when all the PRs are ready.
- **No block at all** is unknown. It merges, because refusing would make the skill useless
  in a project that has not written a block, and says it cannot tell. A later `ship` does
  the live check.
- **A `Deploy:` line** means nothing deploys until someone runs it. It merges and leaves
  the line for `ship`.

## Why it is human-only

The same reason `ship` is: a merge is not undone by closing a tab. `disable-model-invocation:
true` closes the automatic path in the harness, and `flow`, `submit`, `tend`, `sweep`,
`plan` and the agents are told never to call it, which closes the deliberate path. Chat
"merge", a squash-merge by hand through the forge, is a separate thing and stays as it is.
