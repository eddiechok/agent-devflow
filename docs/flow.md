# flow, in detail

What `flow` does after the size is announced. The short version is in the [README](../README.md).

## Changing the PR after you have looked at it

`submit` stops at the pull request. You read it and want something different. Go back through `flow`.

`flow` checks the branch first. It sees the open PR. It treats the request as a **follow-up**. Same branch, same PR. `submit` **updates** it instead of opening a second one.

Follow-up mode reads before it asks. The PR's **Assumptions** and the plan file already hold what you decided the first time. So you are only asked what is genuinely new.

Sizing still runs. A follow-up can be anything from a typo to a rethink. The danger list still applies.

Maybe the thing you want changed is something the **PR itself is reporting**. A check went red. A reviewer asked for something. Then `flow` hands it to `tend` instead of taking it into `build`.

Not every failure a pull request reports belongs to that pull request. `tend` is the step that asks whose it is, before it pushes anything.

The request may turn out to be new work rather than a change to that PR. Then `flow` says so and starts a fresh branch. If a harness pins the branch, it cannot. Then it asks you which you meant.

## Where a Deep plan goes

Deep work writes its plan into the project, at `.devflow/plans/<short-name>.md`. The plan holds the assumptions it took. It also holds the pieces to build. Each piece says whether it depends on another piece, the command that proves it, and a `Done when:` line — the state that means the piece is finished. That last line is there because whoever builds the piece may have nobody to ask.

That file is the spec, not a progress tracker. Its job is to hold the assumptions and the pieces. It is also what `review`'s second axis judges the work against.

**A plan is resumable. The record is `git log`, not the file.** `build` commits each piece as it goes green. So you can `/clear` between pieces and pick up from the plan plus the log. The plan says what the pieces are. The log says which of them exist.

Nothing has to remember to tick a box. That is the reason to trust it. That is also why the checkbox version did not survive.

Commit the file or ignore it, as you prefer. devflow does not add it to `.gitignore`. It does not expect it there either.

## Plans on GitHub

A project can keep its Deep plans as issues instead of files. `setup` asks once and writes:

```markdown
## Plans
- Tracker: github
```

No block, or `local`, means the file. Then:

- `flow` opens an issue with the label `devflow:plan`. The plan is the body. It prints `plan: #45` on its own line.
- `flow` resumes from it after a `/clear`. Only when commits are ahead, so a typo fix never touches the network.
- `review` reads it as the spec, before any file.
- `submit` adds `Closes #45`. The plan closes when the work merges.
- `build` never reads the tracker. `flow` hands it the piece.

Two costs, and `setup` says both out loud. The web sandbox has no `gh`, so a run there falls back to a file and says so. And anyone who can edit the issue can edit the plan. A plan is an order to `build`.

Local and GitHub only. A Linear or Jira ticket is still pasted in as the request.

## The project's words

Some things outlive one job. What this project means by *session*. Or *account*.

They go in a `## Words` block in `CONTEXT.md`, at the project root.

```markdown
## Words
- **Session** — one agent run, start to finish. The browser kind is a *login*.
```

`flow` writes a line there when your answer settles a word. It tells you in one line. Next job, `flow` and `build` read it. Your words show up in the questions, the test names and the commits.

Three rules keep it small and true:

- **Only words you settled.** Never a word the plugin picked itself.
- **Meaning only.** No file paths, no function names. Those rot. A meaning does not.
- **Lazily.** No settled word, no file. `setup` does not create it.

`build` reads it and never writes it. `build` reports a wrong word to you. It does not fix it in silence.

`review` does not get it. `reviewer` must name an input that fails. A bad word cannot fail an input. Give it a style guide and it starts reporting style.

## If it sizes something wrong

```
/devflow:flow --deep <request>
/devflow:flow --quick <request>
```

`flow` records overrides to `~/.claude/devflow/overrides.md`. They go there **globally, not per project**. They are notes about this plugin, not about any one repo. They are only useful when you review them together.

`flow` also prints the line it wrote.

⚠️ On a hosted session that home directory sits inside a container. The container goes away when the session ends. The file does not survive, so the reply is the only copy. Paste it somewhere durable if you work on the web.

Each line is a real example of the classifier getting it wrong, with your correction. After a month you have a set of labelled cases from actual use. That beats any examples invented up front. Do not delete the file.

This is the only self-improvement machinery in Phase 1. It only collects, on purpose. There is no review step yet.

Read the file when it has twenty or so lines in it. See whether a pattern is there. If one is, that is a change to `flow`. Make it through the normal flow, since this repo is just another project.
