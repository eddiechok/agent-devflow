# tend has no guard for the folder it is standing in

`tend` step 1 runs `gh pr checkout <n>`, which moves the whole folder. `flow` has an
entire step 0c to stop exactly this hazard, because a second session open on the same
checkout finds its branch changed underneath it, mid-build, and nothing tells it.

`tend` has nothing. Grepping `skills/tend/SKILL.md` for `worktree`, `folder` or `0c`
returns no hits. It does stop on a dirty working tree, which helps when the other session
has uncommitted work, but not when that session has committed and is simply sitting on a
branch — which is the ordinary case.

The new `ship -> tend` handoff, merged as `028bf66` on 23 Sep 2026, makes this reachable
from a command that does not sound like it moves anything. Before it, a human typed
`/devflow:tend` and could expect the folder to move. Now `/devflow:ship` moves it.

Found by running the handoff for real on PR #32 on 23 Sep 2026, not by reading.

Likely shape: the same two questions `flow` step 0c asks — am I already in a linked
worktree (`git rev-parse --path-format=absolute --git-dir --git-common-dir`), and is this
folder on the default branch — before `gh pr checkout` runs. Note the answer differs from
`flow`'s: `tend` legitimately needs to be on somebody else's branch, so "on the default
branch" is the safe case here rather than the thing to check for. The guard is about
whether *another session* owns this folder, which is not the same question `flow` asks,
so copy the mechanism rather than the conclusion.

Parked from: ship's conflict handoff picks a merge method that cannot work, and nothing tests the path
