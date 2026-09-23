#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own, as
# owner/name. Nothing here can be faked locally, and the reason is narrower than
# `plans-on-tracker`'s: that case needs a real tracker, this one needs a real
# *merge base*. `mergeable: CONFLICTING` is computed by the forge, from a branch
# and a default branch that have both moved. `fixtures/greeter.sh` builds a bare
# repo with no host, where `gh pr view` errors and `ship` stops at step 1 having
# measured nothing.
#
# It does NOT use fixtures/greeter.sh: that fixture inits its own git repo and
# remote, which cannot be done inside a clone. Same reason plans-on-tracker
# skips it, and the layout below is copied from that scaffold.
#
# The conflict is built the way a real one happens -- not by crafting a broken
# merge, but by letting a second change land on the default branch underneath an
# open pull request. That is the only way ship meets one in the wild, and it is
# exactly what happened to #31 and #32 on 23 Sep 2026.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

: "${DEVFLOW_EVAL_REPO:?set DEVFLOW_EVAL_REPO=owner/name to a throwaway repo you own}"

BRANCH="feat/shout-flag"

gh repo clone "$DEVFLOW_EVAL_REPO" "$workspace" -- -q
cd "$workspace"

# Ask the clone rather than assuming `main`: a throwaway repo may well be on
# `master`, and every comparison below is against this ref.
DEFAULT="$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||')"
git checkout -q "$DEFAULT"

# Leave no state from a previous run. The workspace is fresh every time -- the
# runner makes it -- but the remote is not, and a leftover open PR would make
# `ship` step 1 find the wrong one.
gh pr list --head "$BRANCH" --state open --json number --jq '.[].number' \
  | while read -r n; do [ -n "$n" ] && gh pr close "$n" --delete-branch 2>/dev/null || true; done
git push -q origin --delete "$BRANCH" 2>/dev/null || true

mkdir -p src test
cat > package.json <<'JSON'
{ "name": "greeter", "version": "1.0.0", "private": true,
  "scripts": { "test": "node --test" } }
JSON
# One line is the whole fixture. Both sides below rewrite THIS line, which is
# what makes the merge conflict rather than merging cleanly in two files.
cat > src/greet.js <<'JS'
module.exports = (name) => `hello ${name}`;
JS
cat > test/greet.test.js <<'JS'
const test = require("node:test");
const assert = require("node:assert");
const greet = require("../src/greet");
test("greets by name", () => assert.ok(greet("Eddie").toLowerCase().includes("eddie")));
JS
cat > CLAUDE.md <<'MD'
## Checks
- Test: npm test
MD

npm test >/dev/null 2>&1 \
  || { echo "scaffold.sh: npm test does not pass on the fresh fixture" >&2; exit 1; }

git add -A
git diff --cached --quiet || git commit -qm "chore: greeter fixture for the conflict case"
git push -q origin HEAD

# The pull request, cut from the base above and touching the one shared line.
git checkout -q -b "$BRANCH"
cat > src/greet.js <<'JS'
module.exports = (name) => `HELLO ${name.toUpperCase()}`;
JS
git add -A
git commit -qm "feat(greet): add a shouting greeting"
git push -q -u origin "$BRANCH"
gh pr create --base "$DEFAULT" --head "$BRANCH" \
  --title "feat(greet): add a shouting greeting" \
  --body "Upper-cases the greeting. Opened by the ship-tends-conflict eval scaffold." >/dev/null

# Now the second change lands underneath it, on the same line. This is the step
# that makes the open PR conflict, and the order matters: the PR has to exist
# first, or the forge never computes a conflict for it.
git checkout -q "$DEFAULT"
cat > src/greet.js <<'JS'
module.exports = (name) => `hi there, ${name}`;
JS
git add -A
git commit -qm "feat(greet): warmer greeting"
git push -q origin HEAD

# Back onto the PR's branch, and leave the workspace there. `ship` with no
# argument takes the PR for the current branch, which keeps the case's prompt
# free of a number the scaffold would otherwise have to inject.
git checkout -q "$BRANCH"

fail() { echo "scaffold.sh: fixture is broken -- $1" >&2; exit 1; }

# Mergeability is computed asynchronously, so a read taken straight after the
# push comes back UNKNOWN -- which is the very thing ship step 2 refuses to read
# as an answer. If the scaffold handed the case an UNKNOWN, the run would
# measure ship's wait-and-re-read path instead of its handoff, and pass or fail
# for the wrong reason. So block here until the forge has decided.
#
# THIS WAIT IS LOAD-BEARING FOR A GRADER, which is not visible from here.
# `re-reads-all-four-conditions-after-tend` counts step-2-shaped reads and wants
# two: one before the handoff, one on the return. Step 2 mandates exactly one
# before the handoff -- unless mergeability comes back UNKNOWN, whose branch
# says "wait, read once more". Hand the case an UNKNOWN and that second read
# happens before tend is even called, so a run that then dies inside tend scores
# the grader as passed. Delete this loop and that hole opens.
state=""
for _ in $(seq 1 30); do
  state="$(gh pr view --json mergeable --jq .mergeable 2>/dev/null || echo "")"
  [ "$state" = "CONFLICTING" ] && break
  sleep 2
done
[ "$state" = "CONFLICTING" ] \
  || fail "the pull request is '$state', not CONFLICTING -- the case has nothing to hand over"

# The other three of step 2's four conditions must be quiet, or this stops being
# the lone-conflict case and becomes the one ship is supposed to REFUSE to hand
# over. A throwaway repo with a workflow on it would do exactly that, silently.
checks="$(gh pr view --json statusCheckRollup --jq '.statusCheckRollup | length')"
[ "$checks" = "0" ] \
  || fail "the PR reports $checks check(s); ship must stop on those rather than hand over"
reviews="$(gh pr view --json reviewDecision --jq '.reviewDecision')"
[ -z "$reviews" ] || [ "$reviews" = "null" ] \
  || fail "the PR has reviewDecision '$reviews'; that is a second condition, not a lone conflict"

[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || fail "not left on $BRANCH"

echo "scaffold.sh: $BRANCH conflicts with $DEFAULT in $DEVFLOW_EVAL_REPO"
