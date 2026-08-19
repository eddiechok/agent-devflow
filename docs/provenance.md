# Where each idea came from

Every step in devflow, and why it is there.

This is a separate file on purpose. A `SKILL.md` is a prompt — the model reads every line of it, every single time it runs. Notes about where an idea came from would cost tokens on every run forever. They belong here, where a person reads them once, when deciding whether to change something.

**The labels:**

| Label | Means |
|---|---|
| **Copied** | Read it somewhere, kept the idea, wrote it in our own words |
| **Changed** | Read it somewhere, kept the goal, did it a different way |
| **Same idea** | Worked it out here, and a source happens to agree. Not borrowed |
| **Ours** | This repo's own |
| **Real bug** | Came from something that actually broke |
| **Author's note** | The README credits it, but the matching text was not found in the source. Trust it as intent, not as a citation |

**The sources**, all read in full unless noted:

- **superpowers 5.1.0** (Apache-2.0) — `test-driven-development`, `writing-plans`, `requesting-code-review`, `receiving-code-review`, `verification-before-completion`, `finishing-a-development-branch`, `systematic-debugging`
- **[mattpocock/skills](https://github.com/mattpocock/skills)** (MIT) — `code-review`, `tdd`, `grilling`, `implement`, `wayfinder`, `triage`
- **[wshobson/commands](https://github.com/wshobson/commands)** (MIT) — `workflows/git-workflow.md`
- **Anthropic's [`code-review`](https://github.com/anthropics/claude-plugins-official) plugin** (Apache-2.0) — the slash command

---

## `flow`

| Step | From | Why |
|---|---|---|
| Three sizes, Quick / Standard / Deep | **Author's note** — superpowers, with its "never go lighter" rule flipped | The README says so. No three-size classifier was found in superpowers 5.1.0, so it may come from an older version |
| Default down, go heavier only with a reason | **Ours** | The flip itself. Most work is smaller than it first sounds, and a heavy process on a typo teaches people to skip the process |
| Announce the size in one line, first | **Changed** — superpowers announces the skill it is using | Same instinct, more useful content. Which skill is running tells you nothing you can disagree with; a size does |
| All questions in one numbered round, each with a recommended answer | **Copied** — mattpocock's `grilling`: "Ask the whole frontier in one round: number each question and give your recommended answer" | Drip-fed questions turn one job into six turns |
| One round only, then take the recommendations | **Ours** | `grilling` keeps going in rounds as answers unlock more questions. devflow stops after one and moves, because it is trying to finish a change, not design a system |
| Unanswered questions become PR **Assumptions** | **Ours** | Turns a blocking question into a note that can be checked at merge time |
| The danger list | **Ours** | Nothing like it in the three sources |
| Deep work writes a plan file | **Changed** — superpowers `writing-plans` | Same idea, opposite size. Theirs is exhaustive: every step 2-5 minutes, real code in every step, no placeholders. Ours holds the pieces and the assumptions, and nothing that would rot |
| Pieces sized to one reviewable diff | **Changed** — superpowers sizes by minutes of work | A piece is a diff someone has to read, so review is the thing worth optimising |
| "Independent" is stricter than "different files" | **Ours** | The failure it prevents is specific: two pieces that each pass their own tests and break when joined |
| The plan file holds the assumptions and the pieces | **Changed** — superpowers `writing-plans` | Theirs is a document of `- [ ]` steps to work through. Ours holds what was decided and what to build, and doubles as the spec `review`'s second axis reads |
| Size overrides recorded globally | **Ours** | Free labelled data about a classifier that will be wrong sometimes |
| The override line is printed as well as written | **Real bug** — the audit of 18 Aug | On a hosted session `~/.claude` is inside a container that is deleted at the end of it, so every override recorded on the web had been thrown away |
| 0. What the PR reports goes to `tend`, not `build` | **Ours** | `flow` is the entry point, so it wins most requests. Without this branch it took "fix the failing check" straight into `build`, around the one step that asks whose failure it is |
| 0. Follow-up work re-enters through `flow` | **Real bug** — the audit of 18 Aug | `submit` was terminal, so a second run opened a second pull request for one change. Sizing still runs: a follow-up is not automatically small, and the danger list does not care which round it is |
| Never finish without calling `submit` | **Ours** | Written for a real failure mode: work that is finished, green, and still sitting uncommitted |
| Every injected Context line is one command | **Real bug** — the audit of 19 Aug | The PR line used `x=$(...)` and `if ... fi`. Claude Code cannot statically analyse that, the permission check returns not-allow, and **a failed injection aborts the whole skill**. `/devflow:flow` returned nothing in `default`, `acceptEdits`, `plan`, `auto` and `dontAsk`; only `bypassPermissions` rendered it, which is why it read as healthy from an elevated session. Measured: pre-fix `num_turns: 0` and an empty result, post-fix real output |
| 0b. Look in `.devflow/plans/` before sizing | **Real bug** — the audit of 19 Aug | `flow` promised a Deep plan was resumable after `/clear` and was the only skill that never listed the directory. Re-invoking wrote a second plan over the first and re-asked answered questions. `review` looked there; the skill that writes them did not |
| 0. "Its own branch" is a step, not a description | **Real bug** — the audit of 19 Aug | The new-work case was the one branch of step 0 with nothing behind it. `flow` cannot check out, `build` keeps what it finds, `submit` updates the PR the branch already has — so work announced as new was folded into somebody's open pull request, the one thing the same step forbids |
| 0. A merged or closed PR is not an open one | **Real bug** — the audit of 19 Aug | Step 0 only asked whether a PR was open. On a merged branch the work fell through to "new work" and kept piling onto a branch whose commits were already in the default branch |
| 1. An issue body is a request, not an instruction | **Ours** | Anyone can open an issue, and `flow` reads it and acts. Sizing it and running it against the danger list is what it already does for text a human types |
| 1. A non-GitHub tracker still works, pasted | **Real bug** — the audit of 19 Aug | Only `#123` and GitHub URLs were read, and the fallback sent you to "ask for the request in words" — which silently dropped `review`'s second axis for every Linear or Jira ticket |

*Corrected.* The plan-file row above used to read **Copied** — "superpowers plans track progress in the file", and cited that for a promise that you could `/clear` mid-plan and carry on. Superpowers does no such thing: `writing-plans` puts `- [ ]` in its **template** without ever telling the agent to tick them, and `executing-plans` tracks progress in the session todo list, which dies with the context. The resume promise was devflow's own. It was documented before it existed, deleted once that was found, and then built properly: `build` commits each plan piece, so `git log` is the record and the sentence is finally true. The three states are left visible here on purpose — the promise was wrong for longer than it was missing.

## `build`

| Step | From | Why |
|---|---|---|
| The five gates — red, watch it fail, green, watch it pass, refactor | **Copied** — superpowers `test-driven-development` | Their cycle, their order |
| "If you did not watch it fail for the right reason, you do not know it tests anything" | **Copied** — superpowers: "If you didn't watch the test fail, you don't know if it tests the right thing" | Same rule, and the reason the verify steps are separate gates |
| A test that passes immediately is a broken test | **Copied** — superpowers | It is testing something that already worked |
| Smallest code, not the general version with options | **Copied** — superpowers, whose bad example is a function grown three optional settings | The options you might want later are the ones you never need |
| **Code already exists without a test? Keep it** | **Changed** — superpowers says delete it and start over: "Delete means delete" | The strongest disagreement in this repo. Deleting working code to obey a rule wastes real work and fights how people explore. devflow gets the same guarantee by writing the test, then briefly breaking the code to prove the test is real |
| Test at seams, not at every function | **Changed** — mattpocock's `tdd`: "Test only at pre-agreed seams", confirmed with the user first | Same target, one fewer interruption. devflow says which seam it picked in one line and keeps going |
| The tell for testing internals: it breaks on a refactor while behaviour did not change | **Copied** — mattpocock's `tdd` | A test you can check yourself against beats a warning to be careful |
| The expected value must come from outside the code | **Copied** — mattpocock's `tdd` on tautological tests | `expect(add(a, b)).toBe(a + b)` passes because it cannot disagree with the code. It clears every one of the five gates, verify-RED included, so nothing here would have caught it. It matters more in devflow than in a human's hands, because the agent writes the test and the code |
| Full test suite once at the end, not after every edit | **Copied** — mattpocock's `implement`: "typechecking regularly, single test files regularly, and the full test suite once at the end" | A full suite after every edit is slow enough that people stop running it |
| Refactor stays inside the loop | **Copied** — superpowers, and deliberately not mattpocock, who moves refactoring out to review | Cleaning up while the test is green is the payoff for having written it |
| Stop after 2 attempts, report after 3 | **Copied** — superpowers `systematic-debugging`: "3+ failures = architectural problem. Question pattern, don't fix again" | Three failures at one layer usually means the problem is at another |
| Say what each failed attempt ruled out | **Copied** — superpowers | A map of what is not the cause is worth more than a fourth guess |
| A branch someone else named is still a branch | **Real bug** — the edx-landing session | Off the default branch is the requirement. The `<type>/<short-name>` shape is a preference, and a harness that pins the branch outranks a preference |
| `[DBG-` markers, grepped out before finishing | **Ours** | Debug logging is easy to add and easy to forget |
| The marker sweep is `submit`'s command, word for word | **Real bug** — the audit of 18 Aug | `build`'s copy never got the `--exclude-dir` fix, so it walked `node_modules`, where a vendored `[DBG-` is a marker it is told to remove and has no business touching |
| Branch before the first edit | **Ours** | If the job dies later, the edits are not stranded on the default branch |
| A plan piece is committed as it lands | **Ours** | The one case where `build` commits. The plan says what the pieces are and `git log` says which exist, so resuming is answered with evidence. The checkbox-in-the-file version was rejected first: a tick is a claim, and this repo does not take claims |
| Commands come from the project's `## Checks` block | **Ours** | A command invented by a skill is a command nobody verified |
| A change with no behaviour skips the gates and says so | **Real bug** — the audit of 19 Aug | `flow` routes copy, docs, config, styles and images here, and the gates said "no skipping" with no exit. Nothing can go red for a README wording change, so the two available moves were an invented assertion that clears every gate while testing nothing, or a quiet skip that teaches the rest of the skill is optional. This repo is one of the projects that hits it |
| `origin/main` is a fallback, not an answer | **Real bug** — the audit of 19 Aug | `refs/remotes/origin/HEAD` is unset in plenty of working repos. When the fallback fires on a `master` or `develop` repo, "am I on the default branch?" answers no while you are standing on it, and the next commit lands there |
| New work cuts its branch from the default ref | **Real bug** — the audit of 19 Aug | The other half of `flow`'s new-work gap. Cutting from where you stand carries the old branch's commits into the new pull request; staying put hands the work to the old PR |

## `review` skill

| Step | From | Why |
|---|---|---|
| Two axes, reviewed apart | **Copied** — mattpocock | Code can follow every rule and still build the wrong thing. Two reports mean one cannot hide the other |
| 1. Pin the fixed point | **Copied** — mattpocock | You say where to review from, or you get asked. No guessing |
| 1. Check it before spawning | **Copied** — mattpocock | A typo in a branch name should fail in front of you, not inside two agents that find nothing wrong with nothing |
| 1. Count untracked files | **Real bug** — the edx-landing branch | Three new files were never added to git. Both sources look only at commits, so both would have called the branch clean |
| 2. Where to look for the spec | **Changed** — mattpocock | They check issues, then a path, then a few folders. We have one known place: plan file, then issue, then none |
| 2. Never make up requirements | **Copied** — mattpocock | No spec means we say "no spec", not that we imagine one |
| 3. Fresh agents, no session history | **Copied** — superpowers and mattpocock | The session that wrote the code believes everything that went into it |
| 3. 400 word limit | **Copied** — mattpocock | Makes the agent pick its best findings instead of handing you everything |
| 3. Say when the 400 words ran out | **Ours** | The ceiling is meant to drop weak findings, which is fine. Dropping a Blocking one is not, and without a count a truncated review prints exactly like a clean one — the same hole as `NOT RUN` against `none`. **The count is the agent's own word for it and nothing checks it** — better than silence, weaker than evidence, and worth knowing which of the two you are reading |
| 3. Second agent only if there is a spec | **Ours** | A small fix has no spec. One agent, no extra cost |
| 4. Never merge the two reports | **Copied** — mattpocock | One combined score lets a pass on one side cover a fail on the other |
| 5. Reports, never fixes | **Ours** — same split as `build` and `submit` | The part that reads is not the part that writes |
| 3. Say it out loud when the harness blocks the axes | **Real bug** — the edx-landing session of 18 Aug | Claude Code on the web forbids starting an agent unless the human asked. Silence looked exactly like a passing review |
| 4. `NOT RUN` is its own state | **Ours** | `none` means two agents looked and found nothing. Without a separate word, a review that never started prints the same as a clean one |
| 2. Find the plan by listing the directory | **Real bug** — the audit of 18 Aug | Matching a filename against the branch name fails wherever a harness names the branch, which is exactly where Deep work still has a spec to judge against |
| 2. An issue you cannot open is not a spec | **Ours** — the same rule as never inventing one | Skipping the axis is honest. Reviewing against a guessed issue is not |

## `reviewer` agent — is it built right

| Part | From | Why |
|---|---|---|
| An agent, not a prompt template | **Ours**, unlike both sources | Both fill in a template and hand it to a general agent. mattpocock's docs report the cost: those agents found the skill again and kept spawning more, one user hit 50+. Our `tools:` line means this agent cannot spawn or edit anything. A limit, not a request |
| Read the untracked files | **Real bug** — edx-landing | The difference between reviewing a new component and reviewing nothing |
| Name the input that fails | **Changed** — Anthropic's plugin | Theirs scores findings 0-100 and drops anything under 80. A score is still an opinion; "this input gives this wrong answer" can be checked |
| Only two buckets | **Ours** | superpowers uses Critical, Important and Minor. The third bucket is where padding ends up |
| The "do not report" list | **Copied** — Anthropic's plugin | Their false positives: old problems, nitpicks, anything a linter already catches, quality gripes nobody asked for |
| Skip what tools already check | **Same idea** — all three sources say it | `submit` ran the tests and the linter first |
| Missing tests are not a finding | **Ours** | `build` handles tests. The exception, a test deleted or watered down, is on the danger list |
| Check who calls the changed code | **Same idea** — superpowers asks something similar | Written as an action here, because a question gets answered from memory |
| "Nothing found" is a real answer | **Ours**, building on superpowers | Their rule forbids claiming it looks fine without checking. Ours says what to do instead: name what you read |
| Pins `model: opus`, `effort: xhigh` | **Ours** | Neither source pins one. An agent with no `model:` inherits the session, so the same branch gets a different review depending on what the human last typed at `/model`, and the weaker one still reports nothing wrong |

## `spec-reviewer` agent — is it the right thing

| Part | From | Why |
|---|---|---|
| Having this agent at all | **Copied** — mattpocock's spec axis, and superpowers checking work against its plan | devflow wrote plans to `.devflow/plans/` and then never read them again |
| Missing, built wrong, nobody asked for it | **Copied** — mattpocock | Their three kinds of spec finding |
| Scope creep, by name | **Copied** — mattpocock | Neither of the other two has it, and it is what agents actually do |
| Quote the line of the spec | **Copied** — mattpocock | If you cannot point at the line, you made the requirement up |
| A silent spec is not a failing spec | **Ours** | The obvious way this agent goes wrong |
| A later piece is not a missing piece | **Ours** | Deep plans list pieces in order |
| Never judges code quality | **Copied** — mattpocock | If both agents report on style, the split was pointless |
| Pins the same pair as `reviewer` | **Ours** | The two reports are never ranked against each other. Giving one axis a weaker model ranks them anyway, and silently |

## `submit`

| Step | From | Why |
|---|---|---|
| The overall order — verify, review, commit, push, PR | **Copied** — wshobson's `git-workflow`, which is twelve lines long | The whole shape of a git workflow, small enough to read at a glance |
| 1. Branch check as a safety net | **Ours** | `build` should have branched already. This is for when it did not run |
| 1. A branch you were handed counts | **Real bug** — the edx-landing session | The web harness names the branch and forbids pushing to another. Renaming it to fit the convention would break the only push that is allowed |
| 2. Run the checks now, not "they passed earlier" | **Copied** — superpowers `verification-before-completion`: "Evidence before claims, always" | Earlier is not now, and the code changed in between |
| 2. Run each command bare | **Ours** | The hook trims output and prints the exit code, but only for a plain command |
| 3. Grep out the debug markers | **Ours** | Pairs with `build` adding them |
| 4. Run the app, not just the tests | **Ours**, extending superpowers' evidence rule | Tests only check what someone thought to test. A green suite sits happily on top of a broken page |
| 4. Two tries, then stop and say so | **Same idea** — superpowers caps attempts too | An honest failure beats a PR that looks fine |
| 5. Calls `review` instead of reviewing | **Copied** — superpowers splits asking for a review from doing one | Two jobs, two files. It also keeps the review out of the session that wrote the code |
| 5. You may reject a finding, in writing | **Copied** — superpowers' `receiving-code-review` | Their rule: feedback is something to check, not an order. An agent is less accountable than a human reviewer, so a rejection has to be checked, written down, and visible in the PR |
| 5. Scope creep is a decision, not a fix | **Ours** | Quietly deleting work nobody asked for is as bad as quietly keeping it |
| 6. Conventional commits | **Same idea** — wshobson says "following conventions" | Makes `git log` a changelog |
| 7. The PR body shape | **Ours** | **Assumptions** pairs with `flow`'s one round of questions; **How to check this yourself** has to be steps that were actually run |
| 7. Use the preview link if one appeared | **Ours** | A preview is a real build on a clean machine, which catches what a laptop cannot |
| 8. `/code-review` handed to you | **Real bug** — it could not run | Not installed, a slash command a skill cannot type at itself, and it reviews an **open PR**. Step 5 asked for it four steps before a PR existed |
| 8. Never claim a review ran | **Ours** | The old step 5 said `/code-review` "is already installed". A false line in a prompt reads like a finished step |
| 7. Invoking `submit` is the request for the PR | **Real bug** — the edx-landing session | The web harness says not to open a PR unless the human explicitly asked. The skill's own description says it opens one, so typing it is the asking — but somebody had to write that down |
| 7. Blocked PR: push, then hand over the link and the command | **Ours** | The failure mode is silence. Finished, green and invisible is the state this skill exists to prevent |
| 4. Use `run` if it exists, else the project's own way | **Real bug** — the audit of 18 Aug | The same shape as the `/code-review` assertion, which was fixed once as a special case rather than as a rule. Now it is a rule |
| 7. Update the PR when one is already open | **Real bug** — the audit of 18 Aug | A branch has one pull request. The old step opened a second, because it only knew how to create |
| 8. Re-derive the danger list from the diff | **Real bug** — the audit of 18 Aug | `flow` decided it before the code existed and nothing carried the decision here. The loss was silent and it dropped the only security gate in the loop |
| 8. Never merge | **Ours** | The line the whole plugin is built around |
| 2. `exit=N` only comes for a runner the hook knows | **Real bug** — the audit of 19 Aug | The step promised that running bare gets you the exit line. The hook only rewraps commands matching its own list, and this repo's own checks match none of them — so the promise was false in the repo that wrote it, and the gap invites a fabricated `exit=0` |
| 5. `Not reported:` is a finding, not a footnote | **Real bug** — the audit of 19 Aug | Both agents were told to print the line and `review` was told to carry it through. `submit` is the only reader and had no branch for it, so a truncated review printed exactly like a clean one — the same failure `NOT RUN` was written to prevent |
| 7. Some harnesses expect you to press Create PR | **Changed** — was stated as a harness rule | No public prompt or doc says a web session may not open a PR; what is real is a UI expectation. The mitigation was right and the reason was not, so the reason changed and the mitigation stayed |

## `ship`

| Step | From | Why |
|---|---|---|
| The shape — verify, act, clean up | **Same idea** — superpowers `finishing-a-development-branch` | Both end a branch the same way. Theirs offers four options including "push and create PR"; devflow splits that in two, so opening a PR and merging one are never the same keystroke |
| Only a human starts it | **Ours** | `disable-model-invocation: true` in the harness, plus rules in `flow` and `submit`. The first is real, the second is only an instruction |
| Refuse a PR that is red or still running | **Ours** | Starting the skill is consent to merge, not consent to merge anything |
| Match the merge method to the repo's settings | **Ours** | Rebase, squash and merge are already a decision the repo made |
| `git ls-remote` is the oracle | **Real bug** | A real run: the API returned 503 for minutes while `ls-remote` answered fine. When the thing that broke is the API, do not ask the API whether it broke |
| The default branch's SHA, not the branch's absence | **Real bug** | Merging and deleting are separate calls. One run merged, then failed the delete, and a retry loop concluded three times that nothing had merged |
| Any `## Deploy` line may repeat | **Real bug** | The first project that did not fit the one-command shape |
| Fetch the URL after deploying | **Ours** — same reasoning as `submit`'s live check | A green pipeline is not a working site |
| Write the `## Deploy` block only after it worked | **Ours** | The one moment the command is proven is right after it ran |
| A refused branch delete is reported, not retried | **Real bug** — merging this plugin's own audit branch | The web proxy answers `403` to a ref delete while ordinary pushes work. Retrying a policy denial wastes the run; reporting it as a failed merge would be worse |
| `git branch -d` may refuse after a rebase merge | **Real bug** — the same run | Rebase and squash rewrite the commits, so the local branch is not an ancestor of the default branch even though its content is all there. The fix is to check the content landed, never to reach for `-D` |
| Clean up only what this session started | **Same idea** — superpowers refuses to remove a worktree the user still needs | Never kill "whatever is on port 3000" |
| Offer to archive the session, do not archive it | **Ours** | An archived session someone still wanted is an annoyance they have to undo |
| `gh` is the example, not the requirement | **Real bug** — the audit of 18 Aug | `gh` is not pre-installed on Claude Code on the web. The Context line reported the missing CLI as `none for this branch`, so step 1 sent people to `submit` for work that already had an open pull request |
| 1. Keep the PR's head branch by name | **Real bug** — the audit of 19 Aug | `$ARGUMENTS` takes a PR number and nothing resolved it to a branch. `/devflow:ship 12` typed from another branch merged #12 remotely and then deleted the branch you were standing on — unmerged work this session never created |
| 2. A refusal names `tend` | **Real bug** — the audit of 19 Aug | All four refusal conditions are the pull request reporting something, which is `tend`'s job. Stopping without saying so left the only states `ship` refuses with no way out |
| 2. An empty rollup is two different answers | **Real bug** — the audit of 19 Aug | "No CI configured" and "the run has not started" are spelled identically. Reading the second as the first merges commits nothing verified, which is the one thing this step exists to refuse |
| 4. Read the `## Deploy` block before running it | **Ours** | The step executes shell out of a file, holding credentials, touching production, immediately after the least reversible moment in the plugin. Ordinary when you wrote the block; not ordinary on a fork or a first clone |
| 4. A hosted session fails on policy, not on code | **Real bug** — the audit of 19 Aug | A cloud sandbox reaches package registries and GitHub and little else, so the deploy command and the `Verify:` URL both come back blocked. Reporting that as a broken deploy is exactly the misdiagnosis step 5 exists to prevent |

## `tend`

| Step | From | Why |
|---|---|---|
| The skill exists at all | **Ours** | `submit` stopped at the open PR and `ship` refused to merge a red one. Between those two there was nothing, so a red check or a review comment left the loop with no next step |
| 3. Triage before touching anything | **Ours** | The failure a PR reports is not always the PR's. Pushing a fix for someone else's breakage buries the change you are trying to land |
| 3. "Flaky" is what you say after checking | **Ours** | It is the most convenient possible diagnosis, which is exactly why it needs evidence. Re-run once, for a reason you can name |
| 4. Fix through `build`, five gates and all | **Ours** | A CI failure is a bug report with the reproduction attached. That is the easiest test there is to write, so there is no excuse to skip the test |
| 4. Two rounds, then stop | **Same idea** — `build` stops after 3, `submit` reviews at most twice | Three pushes at one red check means the problem is not where you are looking |
| 4. Never weaken a test to go green | **Ours** — it is on the danger list already | The only change worse than leaving the PR red |
| 5. Re-submit rather than push | **Ours** | Pushing from here would skip the fresh checks and the review, which are what make a push worth trusting |
| 6. Answer the thread, do not just push | **Copied** — superpowers `receiving-code-review` treats feedback as something to answer | A silent refusal reads as a miss |
| 1. Check out the PR's branch first | **Real bug** — the audit of 19 Aug | Every later step reads the current branch: triage asks what "this branch" changed, the round counter runs `git log ..HEAD`, `build` keeps what it finds, and `submit` updates the PR *that branch* has. `/devflow:tend 12` from another branch fixed #12's failure onto a different pull request, and left #12 red |
| 3. A conflict or a stale base is yours | **Real bug** — the audit of 19 Aug | `ship` refuses to merge `CONFLICTING` and stops, `flow` sends it here, and this skill only knew about checks and comments. The state had no owner. Merge rather than rebase, because the branch is pushed and a reviewer may be reading it |
| 3. A review comment is a request to size | **Ours** | The skill reads text off a web page and acts on it. "A reviewer asked" is not an override — the danger list does not care who typed the words |

## `setup`

| Step | From | Why |
|---|---|---|
| The whole skill | **Ours** | None of the three sources has one. mattpocock's setup writes an issue-tracker note, a different job |
| Never write a command you have not run | **Same idea** — superpowers' "evidence before claims" | The failure is silent: a wrong command exits 0 and everything downstream reports the work as proven |
| Read the manifest, never guess from convention | **Ours** | `pnpm test` and `npm test` are not interchangeable, and lockfiles say which |
| Do not overwrite an existing block | **Ours** | Someone wrote it deliberately |
| A line may repeat, no wrapper script | **Ours** | Two honest lines beat one invented script. Adding a script is changing the project to suit the tool |

## `test-frontmatter.py`

| Change | From | Why |
|---|---|---|
| Also checks `agents/*.md` | **Ours** | An agent's description is how the right agent gets picked, so a stray `#` cuts it short the same way |
| Agents must pin `model` and `effort` | **Ours** | Both fields are optional and both default to inheriting the session, so leaving them out is spelled exactly like choosing them. `inherit` is rejected for the same reason |
| Booleans compared by YAML spelling | **Real bug** | The parser cross-check compared `str(True)` against `true` and failed both `disable-model-invocation` lines. The suite was red on `main`, in the one test whose job is telling a real mismatch from a file that only looks wrong |

---

## Read, and deliberately not used

Not every source that was read left a mark. These were compared against devflow and passed over, so nobody has to check them again:

| Source | Why not |
|---|---|
| mattpocock's `wayfinder` | Plans work too big for one session as decision tickets on an issue tracker. devflow's Deep plan is one file for one job. Its **fog of war** idea — do not write down a piece you cannot yet state precisely — is the one part worth revisiting if Deep plans start going stale |
| mattpocock's `triage` | Moving issues through labels and states on a tracker. A maintainer's job, not a dev loop |
| mattpocock's twelve-smell baseline in `code-review` | Judgement calls by design, which is the opposite of `reviewer`'s bar: name the input that fails, or drop it |
| mattpocock's `tdd`, on refactoring | They move refactoring out of the loop and into review. devflow keeps it in the loop, with superpowers. Cleaning up while the test is green is the payoff for writing the test first |
| superpowers' Iron Law | Deleting untested code and starting over. See the `build` table — this is the strongest disagreement in the repo |
| superpowers' strengths section in reviews | Praise helps a human trust the rest of the feedback. Nothing reads devflow's review but `submit`, which cannot act on it |
| superpowers' review after every task | Reviewing each task as it lands, to stop errors compounding. A change to `build`, not to `review`, and a bigger bet than the problem so far justifies |

## How much to trust this

The review skill and the two agents were written in one session, so their sources are exact.

The rest — `flow`, `build`, `setup`, `ship`, and the parts of `submit` that were already there — was written earlier by someone else. Every row above was checked by reading the source and the skill side by side, so **Copied** and **Changed** mean the text really does match. What cannot be proven from a file is intent: a rule that matches a source may have been arrived at twice. Where the match was close enough to name, it is named; where it was not, the row says **Ours** or **Same idea**.

One row is weaker than the others, and is marked **Author's note**: the three-size classifier. The README credits superpowers, but superpowers 5.1.0 has no such skill. Either it came from an older version, or from somewhere else. Worth confirming with whoever wrote it.
