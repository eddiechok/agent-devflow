#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block

cd "$workspace"

# The whole case in one line: park the folder on a branch that is somebody
# else's work, the way a second session arriving at a shared checkout finds it.
# No commit on it on purpose -- a branch cut and not yet committed to is the
# commonest shape of the collision, and it keeps `Commits ahead` at 0 so step 0
# settles the follow-up question with git and never reaches for the network.
git checkout -q -b feat/another-session

# Set here, and only here. The shared fixture leaves origin/HEAD unset because
# that is the regression other cases exist to catch -- but an unset one makes
# `Commits ahead` read "unknown", which sends step 0 off to `gh pr view` against
# a bare repo with no GitHub host. That fork has nothing to do with this case
# and would make it flaky for a reason it is not measuring.
git remote set-head origin main

fail() { echo "scaffold.sh: fixture is broken -- $1" >&2; exit 1; }

[ "$(git rev-parse --abbrev-ref HEAD)" = "feat/another-session" ] \
  || fail "not parked on feat/another-session"
[ -z "$(git status --porcelain)" ] || fail "working tree is dirty"
[ "$(git rev-list --count origin/HEAD..HEAD)" = "0" ] \
  || fail "the parked branch is ahead of origin/HEAD, so step 0 will ask gh"
# Absolute, the way step 0c asks for them. Bare, these two disagree in a plain
# checkout entered from a subdirectory, and asserting the broken form here would
# document it as correct.
probe="$(git rev-parse --path-format=absolute --git-dir --git-common-dir)"
[ "$(echo "$probe" | sort -u | wc -l)" -eq 1 ] \
  || fail "the workspace is itself a linked worktree, which step 0c waves through"

echo "scaffold.sh: parked on feat/another-session in $workspace"
