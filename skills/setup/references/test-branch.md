# A test branch?

`setup` step 6e reads this.

Some projects keep `main` live and a throw-away branch that deploys a test site. The PR still
goes to `main`; `submit` also merges the branch into the test branch, so the human checks on
the test site ([test-branch.md](../../submit/references/test-branch.md)). Skip this step with
`– **testsite** skipped — direct mode` in direct mode: there is no PR to test first. When
`## Workflow` already has a `- Test branch:` line, keep it and say what it says.

Otherwise list the remote branches, bare: `git ls-remote --heads origin`. Then ask one
question, in the popup style of step 6:

- **`develop`, `staging` or `dev` is there** → ask about it by name: "Does `develop` deploy a
  test site? What is its link?" Yes, with the link in Other → write
  `- Test branch: <branch> <url>`. No → write `- Test branch: none`, so it is not asked again.
  "Not now" writes nothing.
- **None is there** — a new project that deploys `main` to its test site for now, or no
  remote → still ask: "Will a branch deploy a test site later? Which branch, and what is the
  link?" Yes → write `- Test branch: <branch> <url>` now, before the branch exists: `submit`
  skips it until the branch is on GitHub. "Not now" writes nothing, so a later run asks again.
  "No, never" writes `- Test branch: none`, so it is not asked again.

Setup makes no branch and moves no site. The line goes in the `## Workflow` block of step 6.

Then print what was written, for step 7's report: `✓ **testsite** develop https://test.example.com`,
or `– **testsite** none`, or `– **testsite** not now`.
