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

"Use whatever the session has" came with #129, when `flow` started asking this question in projects set up before step 6a existed ([browser-driver.md](../skills/flow/references/browser-driver.md)). A project with no block is asked on every run, so "no preference" has to be an answer that is written down too: `- Driver: session`, which needs no proof because it names no driver, and which the browser check reads as "use the session's own". A driver that is not installed is the one answer that writes nothing, on purpose. Writing it would break the rule that every block was proven, so `flow` asks again on its next run, until the human installs it.

## Step 6b — why setup asks keep or stop for the dev server

`submit`'s live check starts the project's server. For an app that starts in seconds, stopping it afterwards costs nothing. For one that starts slowly (several servers, a database, a heavy backend such as Medusa), the next click-through pays the whole start again. Only the project knows which it is, so setup reads the start command (`package.json` scripts, a `Makefile` target, a `Procfile`, `docker-compose.yml`, the README's own), marks one answer recommended, and asks once. The answer is a line in `## Workflow`, `- Servers: keep` or `- Servers: stop`. No line means stop, which is what the live check did before the question existed, so a project that never answers loses nothing. A library, a CLI or a one-shot script starts no server and is never asked. `flow` asks the same question once in a project set up before this step existed ([servers-setting.md](../skills/flow/references/servers-setting.md)), because step 1 sends a project that already has `## Workflow` straight past step 6. Keep is best effort and local only; [submit.md](submit.md) and [web.md](web.md) say why.

**The lane recommendation.** A start command that binds one fixed port (`--port 3000`, `PORT=3000`) lets one server run at a time, so a kept server blocks the next live check. Setup prints a recommendation for a lane script and writes nothing, because the script is the project's code and setup writes only the blocks it can prove. The script picks the lowest free lane, every port the app uses moves together, and the CORS or allowed-origins list names every lane. That pattern is the human's own: `scripts/dev.sh` in bykare-medusa-admin, which setup did not invent and credits here. Then the live check reads the port the server printed, since devflow never picks one.

## Step 6c — why setup writes a `.worktreeinclude`

devflow makes many worktrees, and a gitignored `.env` reaches none of them, so a test that needs the database or a live check that starts the server fails there for a reason the change did not cause. The human's own `scripts/sync-worktree-env.sh` in bykare-medusa-admin solved it inside that one project: it links each `.env` from the main checkout into the current worktree, and a run had to remember to call it. Claude Code has the same thing built in. A `.worktreeinclude` at the repo root, in `.gitignore` syntax, names gitignored files it copies into every worktree it makes with git: `claude --worktree`, agents with `isolation: worktree` and the desktop app's sessions ([code.claude.com/docs/en/worktrees](https://code.claude.com/docs/en/worktrees#copy-gitignored-files-into-worktrees)). devflow never runs `git worktree add` itself, so the one file reaches every worktree it makes, the builders' and sweepers' included, and no agent has to link anything.

It copies rather than links. A value changed in the main checkout later does not reach a worktree that already exists, which is fine for worktrees that live as long as one job. A link would follow the change, but it would also let a worktree write back into the main checkout's file.

The question is asked, not assumed, because the file is committed and because an env file can hold keys the human does not want in every agent's folder. "Never copy" writes a file with one comment line, so the answer is kept and the question comes once. Each path gets a leading `/` because a name with no slash matches at any depth, and `.env` alone would copy every `.env` in the tree. Templates (`.env.example`, `.env.sample`, `.env.template`) are left out by name.

The read is paths only. No step opens an env file, and no value goes in a question, a log, the PR or a commit: the paths are all the decision needs.

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
