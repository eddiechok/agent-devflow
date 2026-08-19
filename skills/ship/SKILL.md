---
name: ship
description: "Use after submit, when the pull request is open and you want it finished - merged, deployed, and cleaned up behind it. Merges the PR, runs or watches the deploy, checks the change is really live, then deletes the branch and tidies up the servers, temp files and session. This is the only skill that merges, and only a human can start it."
argument-hint: "[PR number, or blank for the current branch]"
allowed-tools: Bash(git status:*), Bash(git rev-parse:*), Bash(git symbolic-ref:*), Bash(gh pr view:*)
disable-model-invocation: true
---

# ship

Merge it, watch it go live, clean up behind it. You started this, so the merge is yours.

## Context

- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"`
- Default branch ref: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main`
- PR: !`if command -v gh >/dev/null 2>&1; then gh pr view --json number,title,state,mergeStateStatus --jq '"#\(.number) \(.title) [\(.state)/\(.mergeStateStatus)]"' 2>/dev/null || echo "none for this branch"; else echo "no gh here — look the PR up another way"; fi`

**`gh` is the example, not the requirement.** Every `gh` command below names *what to ask for*, not *how to ask*. Use whatever GitHub access this environment has — the CLI, an MCP server, the API. If it has none, say so in one line and stop. Never guess at a PR's state.

Read the Context line the same way. `no gh here` is **not** `none for this branch`: the first says the CLI is missing, the second says the PR is. Only the second is a reason to send someone to `submit`.

## The boundary

`submit` promises **never to merge**, and that promise is worth more than the convenience of breaking it. This skill merges. It is only safe for as long as it cannot be reached without you.

Two separate things keep it that way, and it matters which is which:

- **`disable-model-invocation: true`** closes the automatic path, in the harness rather than by request. Claude will not load this skill because a description looked relevant, it is not preloaded into subagents, and a scheduled task cannot fire it.
- **`flow` and `submit` are told never to call it.** That closes the deliberate path — and it is only an instruction, so it is the weaker half. It is written into their Rules as well as here.

Do not remove either. If you ever see a chain of skills arrive here without a human typing `/devflow:ship`, stop and treat it as a bug in the boundary, not as a convenience.

**One thing to be alert to, because this skill took its name from another.** `ship` used to mean "open a pull request and stop" — the job `submit` now does. Anyone carrying that habit will type `/devflow:ship` expecting a PR and get a merge and a deploy instead. Step 1 catches the common case, since a branch with no PR stops here. It does not catch the case where a PR already exists. If the request sounds like "open a PR", say what this skill actually does before doing it.

## 1. Find the PR

`$ARGUMENTS` is a PR number if you were given one. Otherwise take the PR for the current branch.

**If there is no PR, stop.** Say in one line that the work has not been submitted yet and that `devflow:submit` comes first.

Be sure that is what you are looking at. A missing `gh` is not a missing PR, and telling someone to submit work that already has an open pull request wastes the run and reads as authoritative.

Do not submit and merge in one command. That would run the code review, the live check, the commit, the push, the merge and the deploy without you ever seeing the pull request — which is the one artefact this whole loop exists to put in front of you.

## 2. Refuse a PR that is not ready

Read the state before touching anything:

```
gh pr view <n> --json state,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,title,url
```

Stop and ask if any of these is true:

- the PR is not `OPEN`
- `mergeable` is `CONFLICTING`
- a check failed, **or a check has not finished**
- `reviewDecision` is `CHANGES_REQUESTED`

**A repo with no CI reports no checks at all.** That is not a pending check. Do not stop for it — say "no checks configured" and carry on.

Running this skill is your consent to merge. It is not consent to merge something red, and it is not consent to guess at a check that is still running.

Otherwise print one line and go:

```
PR #2  fix(flow): trigger on any repo change
checks: 3 passed   reviews: none pending
-> merging (rebase), then watching the deploy
```

## 3. Merge

Match the shape the repo already has, rather than always reaching for the same method:

```
gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
```

- Linear history and rebase allowed → `--rebase`, which keeps it linear and preserves each conventional commit
- A branch full of WIP commits → `--squash`
- Otherwise → `--merge`

Delete the remote branch as part of it:

```
gh pr merge <n> --rebase --delete-branch
```

### When the merge command errors

**Find out whether it worked before you react.** GitHub can fail *after* the merge has already landed, and the error looks exactly like one from before it. A blind retry is the wrong move about half the time.

Two real runs, one skill, opposite meanings:

| | Error | Default branch | Branch on remote | Right move |
|---|---|---|---|---|
| Failed **after** the merge | `500` | **moved** | deleted | reconcile locally |
| Failed **before** the merge | `503` | unchanged | still there | retry |

### Ask git, not the API

```
git ls-remote --heads origin
```

**This is the oracle, and it keeps working when `gh` does not.** `ls-remote` speaks the git protocol; `gh pr merge` and `gh pr view` go through the GraphQL API. In a real run the API returned 503 to every call for several minutes while `ls-remote` answered correctly throughout. When the thing that failed is the API, do not ask the API whether it failed.

**The signal is the default branch's SHA.** If it moved, the merge landed.

**It is not whether the branch was deleted.** Merging and deleting are separate calls and either can fail alone — one run merged successfully and then 503'd on the delete, so a retry loop watching the branch concluded "not merged yet" three times about a merge that had already happened. `--delete-branch` is a convenience, not evidence.

### Then

**Merge landed** — do not merge again. Reconcile the local half, which is what usually died: `gh` switches to the default branch and pulls after merging, and a failure there leaves the working tree looking like the work vanished.

```
git fetch origin --prune
git merge --ff-only <default branch ref>
```

If the remote branch outlived the merge, delete it on its own:

```
git push origin --delete <branch>
```

If **that** is refused, see Cleanup below. A branch you could not delete is not a merge that did not land.

**Merge did not land** — retry, with a wait. Cap it. An API that is still down after a few attempts is a finding to report, not something to sit through, and the work is safe either way: the PR is open and the branch is pushed.

## 4. Deploy

Two shapes. Look for a `## Deploy` block in the project's `CLAUDE.md` first — **if it exists, it wins**:

```markdown
## Deploy
- Deploy: npx wrangler deploy
- Verify: https://edxtech.com.my
- Wait: 120s
```

Three rules about the shape, all learned from the first real project that did not fit it:

- **`Deploy` is optional.** Plenty of projects deploy from CI the moment the default branch moves and have nothing to run — then the block carries only `Verify`, which still earns its place by naming what proves it.
- **Any line may repeat.** A deploy is not always one command. Run repeated `Deploy` lines **in order**, stopping at the first failure; treat repeated `Verify` lines as all having to pass.
- **`Verify` may be a URL or a command.** A URL gets fetched and its content checked. A command gets run bare and must exit 0. Not everything that ships is a website, and forcing a filesystem check into a URL field is how a block starts lying.

```markdown
## Deploy
- Deploy: claude plugin marketplace update eddiechok-devflow
- Deploy: claude plugin update devflow@eddiechok-devflow --scope project
- Verify: python3 skills/test-frontmatter.py
- Wait: 60s
```

**With no block**, watch what the forge reports: the deployment status, or the workflow run the merge triggered.

```
gh run watch <id>
```

Either way:

- **Put a time limit on it.** A deploy that never becomes ready is a finding to report, not something to sit through. Say how long you waited.
- **Never hardcode a deploy command here.** Same rule as `## Checks`: the project is the source of truth, and a command invented by this skill is a command nobody verified.
- If there is no block and nothing in CI to watch, **say so in one line** and go to cleanup. Do not invent a deploy so the report looks complete.

If you had to work out what deploying means because the block was missing, **do not write it down yet.** Nothing is proven at this point. Come back to it at the end of step 5, once the deploy has actually worked.

## 5. Check it is really live

A green deploy is not a working site. Fetch the `Verify` URL and confirm **the change you just merged** is actually there, not merely that something answered 200.

Same reasoning as `submit`'s live check: a passing pipeline sitting on top of a broken page is worse than an honest failure, because it ends the conversation instead of starting one.

If it is not live, **say so plainly**, with what you saw. Do not report a successful deploy. The merge is already done and cannot be undone from here, so an accurate report is the entire remaining value of this step.

### If there was no `## Deploy` block, offer to write one now

**Only when the live check just passed.** You have done the one thing nobody could do earlier: run the deploy and watch the URL serve the change. That is evidence `setup` can never collect, because the only way to verify a deploy command is to deploy.

Show what you actually ran, and ask:

```
No ## Deploy block in CLAUDE.md. I just ran:
   Deploy: npx wrangler deploy
   Verify: https://edxtech.com.my  (200, serving the new build)
   Wait:   48s observed, suggest 120s
Write this into CLAUDE.md?
```

Ask rather than assume. From here on that block is what every later run trusts, and a wrong line in it is precisely the silent failure the block exists to prevent.

What may go in it:

- **Only lines you exercised this run.** If the deploy happened on merge and you ran no command, write `Verify` and `Wait` and leave `Deploy` out entirely. An absent line is correct there, not a gap to fill in.
- **One line per command you actually ran.** If it took two, write two. Compressing a two-command deploy onto one line puts a half-truth in the file every later run trusts — which is the failure this block exists to prevent, reintroduced by the thing meant to prevent it.
- **`Wait` from what you observed, rounded up.** Not a guess, and not the exact figure either — that will be too tight on the first slow day.
- **Never a command you did not run.** Same rule `setup` follows, and the reason this offer lives here instead of there.

## 6. Clean up

Only what this session is responsible for.

**Branches.** The remote one usually went with `--delete-branch`. Check rather than assume — `git ls-remote --heads origin` — and delete it on its own if it is still there.

**A refused delete is not a failed merge.** Some environments let you push a ref and refuse to delete one: Claude Code on the web answers `HTTP 403` to the delete while ordinary pushes work all day. Say so in one line, hand the branch to the human, and **do not retry it or look for another way round** — a policy denial is something to report, not something to defeat. Nothing about the merge changes; it already landed and step 7 says so.

Then the local one: switch to the default branch and fast-forward it first, then delete the branch.

**After a rebase or squash merge, `git branch -d` may warn or refuse.** Both methods rewrite the commits, so the branch's SHAs are not ancestors of the default branch even though every line of it is now there. Confirm the content landed — the default branch moved, and the diff is in it — then delete. Never reach for `-D` to make the warning go away. That is how work actually gets lost, and the warning is right more often than the hurry is.

If the merge errored halfway, reconcile against the remote rather than assuming either side is right.

**Dev servers.** Stop only the ones this session started. Never kill "whatever is on port 3000" — that may be something the human is running. The same rule `submit` applies to its live check.

**Temp artifacts.** Remove the screenshots and scratch files the live check wrote to temp directories. Nothing in the repo needs cleaning, because nothing should have been written there in the first place.

**The session.** Once the PR is merged, the session is finished work. **Offer** to archive it. Offer, not do — an archived session the human still wanted open is an annoyance they have to go and undo.

## 7. Report

Short. What merged, whether it is live, what was tidied:

```
Merged #2 (rebase), remote branch deleted.
Deploy: Cloudflare, ready in 48s.
Live: edxtech.com.my serves the new favicon.ico — confirmed.
Cleaned: local branch, dev server on :4321, 3 screenshots in /tmp.
Session: want it archived?
```

## Rules

- Never run without a human starting it. `disable-model-invocation: true` stays, and so does the rule in `flow` and `submit` not to call this.
- Never merge a red PR, or one whose checks have not finished.
- Never merge again on an error before checking whether the merge already landed — the default branch's SHA, read with `git ls-remote`. Not the API, which may be the thing that is broken, and not the branch's absence, which is a separate call that fails separately.
- Never invent a deploy command the project did not give you.
- Never write a `## Deploy` block for a deploy you did not just run and verify in this turn.
- Never call a green pipeline a live check. Fetch the URL.
- Never delete a branch, server or file this session did not create.
- Never report a refused branch delete as a failed merge, and never retry a policy denial.
- Never force-delete a local branch to silence a warning after a rebase or squash merge.
- Never report a deploy as working without the output that proves it.
