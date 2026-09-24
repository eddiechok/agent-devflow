# devflow on Claude Code on the web

What is different on a hosted session, and why each rule reads the way it does. The short version is in the [README](../README.md).


The plugin installs and loads the same way there. Put the `extraKnownMarketplaces` and
`enabledPlugins` block in the repo's own `.claude/settings.json`. Then it comes with the
clone.

But the web harness writes instructions of its own into the system prompt. Three of them
sit on top of devflow's steps.

**You have to start it yourself, and say it in words.** This is the one the plugin cannot
fix.

A web session opens with a task description. That description tells it to make the change,
commit and push. It is a complete loop, already given, before the session reads any skill. A
skill description does not outrank it.

Left alone, the session does the work well and does none of devflow. In the run that
prompted this section it invoked zero skills. It ran no review. It never opened the site.
It opened no PR.

Ask for it as **"use the devflow flow skill"** rather than `/devflow:flow`. A plugin's
skills do not always register as slash commands on the web. The Skill tool works either
way.

The durable version is a prefilled task link: `claude.ai/code?prompt=...&repositories=owner/repo`.
It puts the words in the box for you.

**You may have to ask for the review. But that is your plan, not the web.**

The instruction not to start an agent unless the human asked rides on **Pro**. It fires
locally exactly as it does on the web.

Both review axes are agents. Where that instruction applies, `review` says so in one line
and asks. Say **"run the review"** and both start.

If nothing is said, the axes report `NOT RUN`. `submit` carries that into the PR under
**Known issues**. A blocked review is never a clean one.

On Max or Team, nothing blocks it. That holds on the web and off. The question should
never appear.

**The PR is already asked for.** The harness says not to open a pull request unless the
human explicitly asked. Invoking `submit` *is* that request. So is `flow`, which ends in
it. `submit` says so rather than stopping to ask twice.

**Your branch is already made.** The harness creates it, and forbids pushing anywhere
else. So `build` keeps it instead of making a `<type>/<short-name>` one. Off the default
branch was always the real requirement. The naming was never the point.

**GitHub may refuse to delete the merged branch.** Pushing a ref works. Deleting one answers
`403`. `ship` reports it and hands the branch to you rather than retrying. The merge is
untouched either way. The two are separate calls, which this skill already knew.

**Plans on GitHub work best with `gh` here.** Install it in the setup script, below.
Without it, devflow reaches the plan issue with `curl`. Only when that fails too does
`flow` write the file instead, and it says so on the size line. The resume after a `/clear` then reads the file, not the
tracker. Nothing is lost; the plan is where the web session can reach it.

**`gh` is not pre-installed.** Anthropic's cloud docs say it is. A cloud session on
24 Sep 2026 found no `gh` at all. The web sandbox reaches GitHub through built-in tools
and a credential proxy. Those cover issues, pull requests, diffs and comments with no
setup. So every `gh` command in these skills names *what to ask for*, not *how to ask*.

Add this line to the environment's setup script:

```
apt-get update && apt-get install -y gh
```

It takes about 20 seconds.
`GH_TOKEN` holds a placeholder, and the proxy puts the real credential on each request.
So `gh auth status` says the token is invalid, and requests work anyway.

⚠️ The proxy refuses every GraphQL request with a 403. That is most of `gh`:
`gh issue list`, `gh issue view`, `gh issue create`, `gh label list`, `gh pr list` and
`gh pr view` all fail. `gh issue create` fails too, because it sends GraphQL before it
posts anything. REST gets through: `gh api repos/{owner}/{repo}/...` reads, creates and
closes issues, and `gh label create` works. So plan and backlog issues go through
`gh api`. With no `gh` at all, devflow falls back to `curl`: `GH_TOKEN` still holds the
placeholder, and `curl` to `api.github.com` came back `200` in the same test. Only when
that fails too does a plan go to a file.

Pull requests go the same way. `flow`, `submit` and `tend` find, open, update and read
them through `gh api` too. `gh api` is in no skill's pre-approved tools, because a prefix
rule cannot limit its method or its path. So each call asks first, on your machine too.
`ship` keeps `gh pr`, because `ship` is a local skill (below).

`ship` used to report a missing CLI as `none for this branch`. Those are the same words it
uses for a branch with no pull request. It would send you to `submit` for work that
already had one open. It now tells the two apart.

**`ship` is a local skill.** The default network level on a hosted session reaches package
registries and GitHub, and nothing else. So a deploy command fails on policy rather than
on code. A `Verify:` URL against your own domain fails the same way. Merge from the web if
you like. Run `ship` from your machine.

Nothing here detects the harness. Every rule holds true in both places.
