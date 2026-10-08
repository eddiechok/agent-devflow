# setup, in detail

Why `setup`'s steps are what they are. The steps themselves are in
[the skill](../skills/setup/SKILL.md), and the short version is in the
[README](../README.md).

Every paragraph below was moved here out of `skills/setup/SKILL.md`, word for word. The
skill holds the steps; this holds why they are what they are.

## Why this matters

Everything downstream trusts the `## Checks` block. `build` runs it after every change, `submit` runs it fresh before opening a PR, and the output hook keys off it.

A wrong or stale command here fails **silently**: `submit` runs something harmless, sees exit 0, and reports the work as proven. That is the worst kind of failure in this plugin, so nothing gets written to `CLAUDE.md` until it has actually been run.

## Step 3 — running each command

This is the point of the skill.

### Running them bare

The bash hook trims
the output and prints `exit=N` itself, which is the pass/fail signal you need
here — but only for a plain command. Shape it yourself and the hook steps aside,
and you are back to reading a wall of output and guessing the exit code.

This matters more here than anywhere: a command you cannot read the exit code of
is a command you have not really proven, and proving them is the whole job.

## Step 4 — writing the block

Two honest lines beat one invented wrapper script.

## Step 5 — where plans live

No block means local, and that is the safe outcome without a claim the human did not make.

The second label, `devflow:backlog`, is made alongside `devflow:plan` for the same reason: `flow` needs it the first time a request names more than one feature, and asking for it there would cost a round trip this step can pay for once, up front. A project on `local` gets no label, but `flow` still has somewhere to park the rest — a file under `.devflow/backlog/`.

## Step 0 — reading the repo before asking

A question the repo already answers is a question the human answers for nothing. Whether the
repo is private, how many people can push to it, whether CI exists and whether a push to main
deploys are all facts, so `setup` reads them first and asks only the decision they leave open.
The same rule is `flow`'s: facts are the session's job, decisions are the human's. A `403` or
`404` on branch protection is read as "none" because that is what a free private repo answers.

## Step 6 — why a questionnaire, and why `direct` exists

Some projects gain nothing from a branch and a pull request per job: a private repo one person
uses, with no CI to wait for. For them the PR is a ritual, and `main` is where the work was
going to land anyway. `direct` names that way of working, and `pr` names today's. The names say
how the work is done, not how many people work on the project, so a team can pick `direct` for
a docs repo and a solo project can pick `pr`.

Two questions, not one. The first, what the project is about, goes into `About:` in the
human's own words, so a later session reads a sentence a person wrote rather than a guess.
The second, `direct` or `pr`, is stored because `flow`, the other skills and the hook all
read it later and nothing else carries it.

The recommendation is read from the repo: private, one collaborator and no CI says `direct`,
anything else says `pr`. A push to main that deploys live is a warning in the option's text,
not a reason to change the recommendation, since review still runs on Standard and Deep work.

A project that already has `## Checks` but no `## Workflow` is asked only these questions. A
`## Workflow` that is already there is kept, the same as `## Checks` and `## Plans`: someone
chose it.

## Step 6a — why setup asks for a browser driver, in a UI repo only

`submit` runs a browser check for any UI change, and it has to know which driver to use. A project that names none still gets the check with whatever driver the session has, so this question improves a run and is not a gate on one. The answer is stored in its own `## Browser` block, in the project's CLAUDE.md, and not as a line in `## Checks`, because `build` and `submit` run every `## Checks` line as a command and a driver's name is not one.

It is asked in a UI repo only, by the skills skill's own read of one (react-native, expo, electron or tauri, a tailwind config, a `components/ui` folder), so a backend never sees it. One question, three options. Playwright CLI is recommended because Microsoft's own notes say a CLI call avoids loading large tool schemas and verbose accessibility trees into context, which is a cost every check would otherwise pay; no source measures it per action, so that is the reason given and no more. "Research which fits me" starts one `devflow:researcher` and only when the human picks it, so no one pays for research they did not ask for. "Other" is the human's own driver.

The driver is proven before the block is written, for the same reason every check command is: a block nobody ran is a claim, and `submit` would trust it. A driver that is not installed gets its install command printed and is not installed, since setup installs nothing (step 8 makes the same offer and leaves the install to the human). That meant changing two rules that said setup writes the Checks, Plans and Workflow blocks and nothing else: they now allow this one block, in a UI repo, once it is proven.

## Why the `disable-model-invocation` flag came off

`flow` runs `setup` first when `CLAUDE.md` has no `## Workflow` block. A skill with
`disable-model-invocation: true` cannot be called by another skill: the Skill tool refuses it
and tells the model to ask the human to type it, even when a skill's own instructions say to
call it ([anthropics/claude-code#93761](https://github.com/anthropics/claude-code/issues/93761)).
So the flag came off `setup`. `ship` and `sweep` keep theirs, because they should only ever
start from a human.

## Step 8 — why setup offers `devflow:skills`

Setup is the one moment a project is looked at as a whole, so it is the natural place to
ask which agent skills would fit it. The human asked for that on #96. `devflow:skills`
already does the reading and the listing, and it is model-invocable, so setup calls it
rather than copying it. It comes after the report, so the list is the last thing on screen,
and only on a yes: a project set up again later can skip it in one answer. Nothing gets
installed here. `skills` prints each command, and the human decides which to run.

## Where the shape came from

The questionnaire follows `setup-matt-pocock-skills` in
[mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md)
(MIT). That skill is not forced on the user. This one is run by `flow` when the block is
missing, because the block is read by every skill and the hook.
