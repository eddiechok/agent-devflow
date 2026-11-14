# scout, in detail

Why `scout` is what it is. The steps themselves are in
[the skill](../skills/scout/SKILL.md), and where each idea came from is in
[provenance](provenance.md).

`sweep` and `dispatch` take only issues that already exist. Nothing found work nobody had
asked for yet; `scout` does, and files it as issues for a human to approve.

## Why a human starts it, and a human approves what it files

`scout` carries `disable-model-invocation: true`, like `sweep`: only you, or a routine you
made, starts it. Every tool checked while designing it (Jules, Copilot Autofix, Claude Code
Review) keeps a human between the finding and the fix; none finds and fixes with no gate.

So what `scout` files waits. Every issue carries the label `devflow:found`, and `sweep` and
`dispatch` skip it as "waiting for approval". **You approve a finding by removing the label.**
One label, one action. This matters because `sweep` trusts any author with write access, and
`scout` files under your account, so without the label its issues would pass `sweep`'s trust
filter and be built the same run. `scout` itself never removes the label, and never comments
on, edits or closes an issue.

## Why levels, copied from improve

`quick`, `standard` and `deep` are [shadcn/improve](https://github.com/shadcn/improve)'s table:
hotspots only, hotspot-weighted, or the whole repo. A plain `/devflow:scout` is `standard`.
The level changes how much of the repo is read and how many agents read it, never the rules:
at every level `scout` files at most 5 issues, never edits code, and never asks which
findings to keep. An unattended routine gets the same behaviour as a run by hand, so the one
thing that could differ, a question, never exists.

The 5 is a cap on a human's reading time: a routine that filed 40 issues would be closed
unread. What is over the cap stays in the report, ranked by harm and not by age.

## Why every finding is checked twice

Subagents over-report: a by-design behaviour called a bug, the wrong line, a duplicate.
`scout` opens the cited code itself first (improve's step), then starts `hardcase`, which
traces where each input really comes from and argues the finding is false before it stands.
Only what `hardcase` lets stand goes on to be filed. A false issue costs a human the time to
close it, and a routine that files false issues is switched off.

## Why packages and the runtime are checked live

A model's training ends before the newest CVEs and releases. The Node.js November 2026
release, the React Server Components flaw and the PHP flaws of this autumn are all after it,
so reading the repo and answering from memory finds none of them. Only a live source can.

- **Packages:** Dependabot alerts first, because GitHub already has the list for this repo.
  Then OSV-Scanner when it is installed, which reads the lockfiles. Otherwise `scout` says
  `packages not checked` and why. It never turns Dependabot alerts on: that is a setting of
  your repo, not something a read-only audit changes. A reachability read then drops an alert
  whose vulnerable code path the repo never uses.
- **Runtime:** the model finds the runtime and version in the repo by file (`.nvmrc`, a
  Dockerfile, `go.mod`, ...), with no list hardcoded in the skill, then asks
  [endoflife.date](https://endoflife.date/docs/api/) for that cycle's `isEol` and `latest`.

These run at every level, even `quick`, because they cost two calls and the newest hole is
the one no code read finds.

## Why a public repo's security finding is a draft advisory

An issue in a public repo is public. Filing "SQL built from a request field in `api.js`"
there publishes the hole before anyone fixed it. So in a public repo a security finding goes
to a draft repository security advisory (`POST repos/{owner}/{repo}/security-advisories`),
which only the repo's security managers and admins see. In a private repo it is a normal
issue. If the advisory call fails, because the token is not allowed to make one, the finding
stays in the report and never falls back to an issue. If the visibility call fails, the repo
is treated as public. `sweep` and `dispatch` do not act on draft advisories: you handle them.

## Why a hidden marker

Each issue body and advisory carries `<!-- devflow:scout <fingerprint> -->`, a short hash of
the category, the file and the thing it is about, never a line number. Before filing, `scout`
lists issues of every state and advisories, and skips a fingerprint already there. The label
is no help for this: you remove it to approve. Closed means rejected, so a finding you turned
down is never filed again.

## Setting it up on a schedule

A routine runs `scout` in the cloud. Set it up with the steps in #184. A cloud environment
has Limited network access, and its default allowed hosts do not include `endoflife.date` or
`api.osv.dev`, so add both under the environment's **Allowed domains**. Until you do, a
blocked call fails and `scout` prints `packages not checked` or `runtime not checked` with the
reason and carries on; everything else still runs. GitHub goes through a separate proxy that
refuses GraphQL, which is why `scout` uses `gh api` and never `gh issue`.

`setup` does not offer to make a scout routine yet; that belongs to #184.
