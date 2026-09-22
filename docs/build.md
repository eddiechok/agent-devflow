# build, in detail

Why `build`'s gates are what they are. The steps themselves are in
[the skill](../skills/build/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/build/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

## Running the checks bare

The bash hook trims long check output and prints `exit=N` itself — but only for
a plain command, and only for the runners on its own list. Shape it yourself and
the hook steps aside by design, and you lose the trimming *and* the exit line.
Doing it by hand is fragile anyway: `${PIPESTATUS[0]}` after a `;` silently
printed nothing in a real run, because the shell was not the one that syntax
assumes.

## The project's words

`flow` wrote it when the human settled a word. Only `flow` writes it, because only `flow`
asks the human. Most projects get one only after a Deep job settles the first word.

## Getting off the default branch

Do the stripping yourself rather than piping through `sed` — a pipe here costs a permission prompt for `sed` on top of the git command, in every project, forever.

**`origin/main` is a fallback, not an answer.** `refs/remotes/origin/HEAD` is only set if
the repo was cloned or somebody ran `git remote set-head`, and plenty of working repos have
neither. When it is unset the `|| echo origin/main` fires and you are **guessing**, so on a
repo whose default branch is `master`, `develop` or `trunk`, "am I on the default branch?"
answers no while you stand on it, and the next commit goes straight there. If the fallback
fired, find the real default before comparing — `git remote show origin` says it, and so
does the forge — or say in one line that you could not, and branch anyway. Branching when
you did not need to costs nothing; the other mistake is the one the hook exists to catch.

One someone else named, or one a harness created for you, satisfies this step as well as one you would have named. Renaming it can break a harness that pins where you are allowed to push.

**One exception, and it is narrow: you were told this is new work.** `flow` decides that,
and only `flow` can — the branch alone cannot tell you, because a branch with a merged PR
and a branch mid-feature look identical from here.

Cutting it from here instead would carry the old branch's commits into the new pull
request. And staying put is worse: `submit` finds the pull request already open for this
branch and updates it, which bolts unrelated work onto somebody's PR.

`submit` checks this too, but by then it is late. Editing happens here, and `submit` is several gates away — if it never runs because you got stuck, the checks stayed red, or the human stopped you, the edits are left sitting uncommitted on the default branch. Branching first costs one command and the abort case stays clean.

## When there is nothing a test could catch

`flow` routes copy, content, docs, config, styles and images here as readily as code, so
the answer is genuinely no often enough that it needs an answer. There is no test that can
go red for a README wording change, an image swap, a colour token, an `.env.example` line
or a Terraform variable — and a whole repo can be like that, this plugin included.

That is a real answer and it is the honest one. The two failures it exists to prevent are
both worse:

- **An invented assertion.** `expect(readme).toContain("Install")` goes red before the edit
  and green after, so gate 2 and gate 4 both pass and nothing was ever tested. It is the
  same defect as the tautological test below, arriving through a door the gates leave open.
- **Skipping quietly.** A skill that says "no skipping" and then gets skipped teaches that
  the rest of it is optional too.

## Gate 1 — where the expected value comes from

That one passes verify-RED as well — the function does not exist yet, so it fails, and it fails for the right reason. Every gate goes green and nothing was ever tested. You are the one writing both sides here, which is exactly why this is easy to do by accident.

## Gate 2 — watching it fail

> If you did not watch it fail for the right reason, you do not know it tests anything.

## Code that already exists without a test

That wastes work and fights how people actually explore.

## When you get stuck

A clear "I am stuck, here is the map" is worth more than a fourth guess.

## Debug markers

Markdown is excluded because a marker there is a code sample, not something that runs — `submit` step 3 skips it for the same reason, and keeps the quotes for the same reason too: zsh expands a bare `*.md` and the command dies before grep sees it.

## Committing a plan piece

**This is the only case where `build` commits**, and the reason is narrow. A Quick or Standard change is one piece, and `submit` commits it after the checks and the review, which is where that belongs. A plan is several pieces across a job long enough to outlive the context that started it, and a commit per piece is what makes it resumable: `git log <default branch ref>..HEAD` then answers *which pieces are built* with evidence, rather than a checkbox somebody had to remember to tick.
