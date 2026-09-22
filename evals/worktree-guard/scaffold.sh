#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block

cd "$workspace"

# The whole case in one line: park the folder on a branch that is somebody
# else's work, the way a second session arriving at a shared checkout finds it.
#
# With a real commit on it, and not an empty branch. The first version of this
# fixture left the branch at main's tip, which made every branch in the
# workspace the same SHA -- so a worktree cut from the default ref and one cut
# from HEAD produced identical trees and the case could not tell them apart.
# That is the half of the guard worth measuring: `worktree.baseRef` is `head` on
# any machine where `flow` has written it, so a session that keeps the branch
# EnterWorktree opened is building on this commit without knowing.
git checkout -q -b feat/another-session
cat > OTHER_SESSION.md <<'MD'
# Not this request's work

A commit that exists only on feat/another-session. A feature branch cut from the
default ref must not contain it; one cut from HEAD will.
MD
git add -A
git commit -qm "docs: the other session's work in progress"

# Set here, and only here. The shared fixture leaves origin/HEAD unset because
# that is the regression other cases exist to catch, but an unset one makes the
# `Default branch ref` Context line a guess, and this case is about comparing
# the parked branch against that ref.
#
# It no longer keeps step 0 off the network, and an earlier version of this
# comment claimed it did. The commit above puts `Commits ahead` at 1, so step 0
# asks `gh pr view` against a bare repo with no host and gets an error. That is
# a handled path, not a fork out of the case: `skills/flow/SKILL.md:38` gates
# the follow-up branch on the branch *having an open pull request*, and an
# erroring `gh` produces none, so `:48` and `:61-63` send an ambiguous branch
# down "new work, fresh branch" -- which is exactly what step 0c is scoped to at
# `:188`. Step 0b makes no call at all here; its `gh issue list` is gated on a
# `## Plans` block saying `github`, and the shared fixture's CLAUDE.md has only
# `## Checks`. The cost is a few wasted tool calls, which is what `max_turns:
# 20` is for. Measured: 3 runs, 3 passes, 14/14 weighted each.
git remote set-head origin main

fail() { echo "scaffold.sh: fixture is broken -- $1" >&2; exit 1; }

[ "$(git rev-parse --abbrev-ref HEAD)" = "feat/another-session" ] \
  || fail "not parked on feat/another-session"
[ -z "$(git status --porcelain)" ] || fail "working tree is dirty"

# The divergence is the point, so assert it rather than assuming it held.
[ "$(git rev-list --count origin/main..HEAD)" = "1" ] \
  || fail "feat/another-session does not diverge from main, so a wrong base is invisible"
git cat-file -e "origin/main:OTHER_SESSION.md" 2>/dev/null \
  && fail "OTHER_SESSION.md is on main too, so it cannot tell the two bases apart"
# Absolute, the way step 0c asks for them. Bare, these two disagree in a plain
# checkout entered from a subdirectory, and asserting the broken form here would
# document it as correct.
probe="$(git rev-parse --path-format=absolute --git-dir --git-common-dir)"
[ "$(echo "$probe" | sort -u | wc -l)" -eq 1 ] \
  || fail "the workspace is itself a linked worktree, which step 0c waves through"

echo "scaffold.sh: parked on feat/another-session in $workspace"
