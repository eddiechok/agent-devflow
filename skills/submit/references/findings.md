# Act on what the review found

`submit` step 5 reads this when the review reported a finding, an axis `NOT RUN`, or a `Not reported:` line.

Then act on what comes back:

- **Blocking**, **Exploitable**, **Missing** and **Built wrong** — fix, then review again. At most **2 rounds**. `Exploitable` is `security-reviewer`'s own bar, and it is fixed on the same footing as `Blocking`, not weighed as a lesser finding.
- **Round 2 is scoped, not a fresh review.** It goes to the axis agent directly — `devflow:reviewer` for its own findings, `devflow:security-reviewer` for its own, or `devflow:spec-reviewer` for its own — with the fixed point, round 1's findings in the agent's own words, and the files changed since.
- **One bug, one fix.** When `reviewer` and `security-reviewer` name the same line for the same flaw, it is one finding: fix it once and list it once.
- **Nobody asked for this** — either take it out, or keep it and say why in the PR under **Assumptions**. Silently keeping it is not an option.
- Anything still standing after 2 rounds goes in the PR under **Known issues**, not hidden and not looped on forever.
- **The last review must postdate the last edit.** A fix you make after the last round is an edit nobody has read, and so is a doc fix at step 6. Both get one short look at step 7, before the commit. It is a look, not a round.
- **`NOT RUN`** — an axis that could not start is not a passing axis. Name it under **Known issues**, and say in **Evidence** which axes ran, which were `NOT RUN`, and which were `skipped` — `security-reviewer` skipped for no security item touched reads the same way `skipped — no behaviour` does, and neither is a finding. Never write "reviewed" over a review that did not happen.
- **`Not reported: N further findings`** — the axis ran out of room. Those findings exist and you have not seen them. **Run that axis again, scoped to what it did not reach**, and if the second run is also truncated, say so under **Known issues** with the count.

**A finding can be wrong, and you are allowed to say so.** Check it against the code first, then reject it in one line with the technical reason, and put the rejection in the PR under **Known issues** so the call is visible to whoever merges. Never reject a finding you have not checked, and never reject one silently — an unread finding quietly dropped is worse than a false positive fixed.

**The `Challenged` section is help with exactly that call, not a decision already made.**

- **Falls** — `hardcase` found the line that refutes it. **Check that line yourself**, then reject the finding with its reason.
- **Stands** — a finding that survived an agent whose whole job was to break it. Fix it. Rejecting one of these takes more than a one-line reason, and you had better be able to say what both of them missed.
- **Could not check** — the challenge did not happen for that finding. Treat it exactly as if there had been no challenge at all. It is not a `Falls`.

Never write "challenged" over a `hardcase` that did not run, and never let a `Falls` you did not verify take a fix off the list.
