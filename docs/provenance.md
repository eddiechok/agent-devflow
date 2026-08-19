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
| 0. Follow-up work re-enters through `flow` | **Real bug** — the audit of 18 Aug | `submit` was terminal, so a second run opened a second pull request for one change. Sizing still runs: a follow-up is not automatically small, and the danger list does not care which round it is |
| Never finish without calling `submit` | **Ours** | Written for a real failure mode: work that is finished, green, and still sitting uncommitted |

*Corrected.* The plan-file row above used to read **Copied** — "superpowers plans track progress in the file", and cited that for a promise that you could `/clear` mid-plan and carry on. Superpowers does no such thing: `writing-plans` puts `- [ ]` in its **template** without ever telling the agent to tick them, and `executing-plans` tracks progress in the session todo list, which dies with the context. The resume promise was devflow's own, it was never built, and it is now on the not-yet list instead of in the docs as a feature.

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
| Commands come from the project's `## Checks` block | **Ours** | A command invented by a skill is a command nobody verified |

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
| Clean up only what this session started | **Same idea** — superpowers refuses to remove a worktree the user still needs | Never kill "whatever is on port 3000" |
| Offer to archive the session, do not archive it | **Ours** | An archived session someone still wanted is an annoyance they have to undo |
| `gh` is the example, not the requirement | **Real bug** — the audit of 18 Aug | There is no `gh` on Claude Code on the web. The Context line reported the missing CLI as `none for this branch`, so step 1 sent people to `submit` for work that already had an open pull request |

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
