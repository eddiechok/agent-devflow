# ship, in detail

Why `ship`'s steps are what they are. The steps themselves are in
[the skill](../skills/ship/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/ship/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

## The Context block

**Keep that line a single command.** An injected command Claude Code cannot statically
analyse fails its permission check, and a failed injection **aborts the whole skill** —
Claude never sees one word of this file, and `/devflow:ship` does nothing at all. `if ...
fi` and `x=$(...)` both do it. A `||` fallback is fine. Do not put the shell branching
back; it belongs below, where the model does it.

### Asking GitHub for the PR's state

Every `gh` command below names *what to ask for*, not *how to ask*.

## The boundary

`submit` promises **never to merge**, and that promise is worth more than the convenience of breaking it. This skill merges. It is only safe for as long as it cannot be reached without you.

Of the two things that keep it that way, the first closes the automatic path:

Claude will not load this skill because a description looked relevant, it is not preloaded into subagents, and a scheduled task cannot fire it.

### The name this skill took from another

Anyone carrying that habit will type `/devflow:ship` expecting a PR and get a merge and a deploy instead. Step 1 catches the common case, since a branch with no PR stops here. It does not catch the case where a PR already exists.

## Step 1 — the PR and its head branch

`headRefName` is in the Context line for this reason. Step 6 deletes a branch, and "the local one" means *this PR's* branch, never whichever one you happen to be standing on — `/devflow:ship 12` typed from `fix/logging` merges #12 remotely and would otherwise delete `fix/logging`, which is unmerged work this session did not create.

Be sure that is what you are looking at. A missing `gh` is not a missing PR, and telling someone to submit work that already has an open pull request wastes the run and reads as authoritative.

Do not submit and merge in one command. That would run the code review, the live check, the commit, the push, the merge and the deploy without you ever seeing the pull request — which is the one artefact this whole loop exists to put in front of you.

### Stacked pull requests

On 22 September 2026, `gh pr merge 23 --rebase --delete-branch` closed #24 as a side effect. #24 was stacked on #23's branch — its base was `feat/review-no-behaviour-exit`, not `main` — and deleting that branch in the same call as the merge closed it. GitHub did not retarget it. Once the base branch was gone, `gh pr edit --base main` answered "Cannot change the base branch of a closed pull request" and `gh pr reopen` answered "Could not open the pull request". The only way out was a fresh PR for the same branch, #25, with a body that pointed back at #24.

Two rules follow. A PR whose base is not the default branch is not `ship`'s to merge: merging it lands it inside the base PR, the deploy runs on nothing, and the human reviewed the base PR as one thing. So `ship` says it is stacked, names the base PR, and stops. And a PR that other open PRs are based on is merged **without** `--delete-branch`; each stacked PR is pointed at the default branch with `gh pr edit --base` and checked still open, and only then is the branch deleted. GitHub retargets a stacked PR itself only while the base branch still exists, and `--delete-branch` removes that window.

## Step 2 — what running this skill consents to

Running this skill is your consent to merge. It is not consent to merge something red, and it is not consent to guess at a check that is still running.

**It is also your consent to have a conflict resolved on the way**, which is the one of step 2's four refusals that `ship` now hands to `devflow:tend` itself rather than stopping on.

The four are not alike, and treating them alike is what made this worth changing. A red check may be this branch's fault or somebody else's. A reviewer asking for changes wants an answer, not a patch. A PR that is not `OPEN` is not shippable at all. Every one of those is a **judgement call**, and a judgement call belongs to you.

A conflict is not. It is what happens when another pull request merges first — which is to say it is a fact about the clock, not about the branch. `tend` already knew how to fix it: merge the default branch in, read both sides, re-submit. And re-submitting means `review`'s two agents, which never saw the session that wrote the resolution, read it before it comes back. So the fix is mechanical and it arrives reviewed, and making you type `/devflow:tend 32` bought nothing but the typing. That is exactly what shipping #31 and #32 looked like on 23 Sep 2026: two branches cut from the same commit, the second conflicting the moment the first landed.

**One attempt, never two.** A conflict `tend` could not settle is one a second `tend` will not settle either, and a loop here rewrites a branch repeatedly with nothing to show for it.

**The direction is what keeps the boundary intact.** `disable-model-invocation: true` and the rule in `flow` and `submit` never to call `ship` are both about nothing *reaching* this skill without you. Reaching outward is the other direction, and `tend` never calls back — its own Rules forbid it. What genuinely changed is the description: merging is no longer all this skill does, and step 7's report has a `Tended:` line because you asked for a merge and should not find a rewritten branch afterwards without being told.

`flow`'s chain loop keeps its hard stop on a merge conflict, and that is not an inconsistency. There, a conflict means two chains edited one file, which the plan promised they would not — so the conflict is a planning bug, and resolving the merge would bury it. Different cause, different answer.

## Step 3 — the two real merge-error runs

**Find out whether it worked before you react.** GitHub can fail *after* the merge has already landed, and the error looks exactly like one from before it. A blind retry is the wrong move about half the time.

### Ask git, not the API

**This is the oracle, and it keeps working when `gh` does not.** `ls-remote` speaks the git protocol; `gh pr merge` and `gh pr view` go through the GraphQL API. In a real run the API returned 503 to every call for several minutes while `ls-remote` answered correctly throughout. When the thing that failed is the API, do not ask the API whether it failed.

**It is not whether the branch was deleted.** Merging and deleting are separate calls and either can fail alone — one run merged successfully and then 503'd on the delete, so a retry loop watching the branch concluded "not merged yet" three times about a merge that had already happened. `--delete-branch` is a convenience, not evidence.

### Then

**Merge landed** — do not merge again. Reconcile the local half, which is what usually died: `gh` switches to the default branch and pulls after merging, and a failure there leaves the working tree looking like the work vanished.

**Merge did not land** — retry, with a wait. Cap it. An API that is still down after a few attempts is a finding to report, not something to sit through, and the work is safe either way: the PR is open and the branch is pushed.

## Step 4 — the deploy block

Deploy commands hold credentials and touch production, and this
step fires immediately after a merge, which is the least reversible moment in the plugin.

The merge
has already landed and cannot be undone from here; not deploying is recoverable, and this
is the one place where refusing costs nothing.

### When the block is blocked, not broken

Say which one you hit and stop — reporting a broken deploy for a proxy denial is
exactly the misdiagnosis step 5 exists to prevent.

### `Verify` as a URL or a command

Not everything that ships is a website, and forcing a filesystem check into a URL field is how a block starts lying.

## Step 5 — the live check

**Only first-hand ends this step**, and here it matters more than anywhere else in the
plugin: the merge has already landed and cannot be undone from here, so an accurate report
is the entire remaining value of the step. Reporting second-hand evidence as proof does not
just overstate — it closes the conversation that would have caught it.

A passing pipeline sitting on top of a broken page is worse than an honest failure.

The merge is already done and cannot be undone from here, so an accurate report is the entire remaining value of this step.

### Offering to write a `## Deploy` block

You have done the one thing nobody could do earlier: run the deploy and watch the URL serve the change. That is evidence `setup` can never collect, because the only way to verify a deploy command is to deploy.

From here on that block is what every later run trusts, and a wrong line in it is precisely the silent failure the block exists to prevent.

Compressing a two-command deploy onto one line puts a half-truth in the file every later run trusts — which is the failure this block exists to prevent, reintroduced by the thing meant to prevent it.

## Step 6 — cleaning up

Nothing about the merge changes; it already landed and step 7 says so.

### After a rebase or squash merge

Both methods rewrite the commits, so the branch's SHAs are not ancestors of the default branch even though every line of it is now there.

That is how work actually gets lost, and the warning is right more often than the hurry is.
