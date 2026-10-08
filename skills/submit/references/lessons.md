# A fact worth keeping is not always about devflow

`submit` step 6 reads this when the run learned something worth keeping.

Two kinds of lesson, and this run is the only one that can tell them apart — no subagent
does this sort, because a fresh agent was not there for the mistake.

**A fact about this project** — "the tests need the sandbox key", something the next run
on this repo would get wrong without it, and that no `CLAUDE.md` or `.claude/rules/` file
already says — gets one line, in this same commit, so the human approves it with the work
rather than discovering it cold on a later run. List it under **What** in the PR body too.

Where the line goes depends on the files the fact is about:

- **One package.** The package is the nearest folder above those files that has its own
  package file — `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` or the like.
  When that folder is not the repo root, the line goes to `.claude/rules/<package>.md`,
  with `<package>` the folder's path, `/` written as `-` (`apps/backend` →
  `apps-backend.md`). No such file yet → make it, starting with this frontmatter:

  ```markdown
  ---
  paths: <package>/**
  ---
  ```

  An existing `.claude/rules/` file whose `paths:` already covers those files takes the
  line instead.
- **Anything else** — the package is the repo root, the fact spans packages, or it is
  about no file — goes to the root CLAUDE.md.

Before writing a rule file, `git check-ignore -q .claude/rules/<package>.md`. Ignored →
the root CLAUDE.md instead, since a file nobody commits is lost with the checkout.

Print the file it went to, with `(new)` when you made it:

```
✓ **lesson** added to CLAUDE.md — the tests need the sandbox key
```

```
✓ **lesson** added to .claude/rules/apps-backend.md (new) — restart after CORS
```

Nothing to add → print nothing. This is not step 6's `docs` line, and does not replace it.

**A fact about devflow itself** — `flow` sized something wrong, a review finding fell,
a deploy's `Verify` failed — never goes into `CLAUDE.md`. Call `devflow:lesson` instead;
`flow`, `review` and `ship` already call it on their own clear signs, so this is only for
one your own run noticed that none of them did.
