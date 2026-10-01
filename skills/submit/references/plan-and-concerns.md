# A plan issue, and a Deep branch's concerns

`submit` step 7 reads this when the work has a plan — a `devflow:plan` issue, or a Deep branch built by `builder` agents.

## At the commit

**A Deep branch may already be committed.** If there is nothing to commit, print `– **commit** nothing to commit — already committed by build` and go on. Never make an empty commit to have something to show for the step.

## In the PR body

**A plan issue closes with the PR.** Only if the project's `## Plans` block says `github` and this work has a `devflow:plan` issue. Then name it under **What** — `Plan: #45` — and add `Closes #45` under **Why**, beside the request issue if there is one. Find the number on the `✓ **plan** #N` line `flow` printed, or by listing open `devflow:plan` issues and matching the subject. Do not guess a number, and write nothing about a plan issue on a project that keeps plans in files.

**A Deep branch carries assumptions in its commits too.** Each `builder` writes any doubt
it had about a finished piece as a `Concern:` line in that piece's commit body, because
the session that printed it may have been cleared since. Read them out:

```
git log <default branch ref>..HEAD --format='%h %s%n%b'
```

Every `Concern:` line goes under **Assumptions**, one bullet each, with the subject of the
commit it sits under.
