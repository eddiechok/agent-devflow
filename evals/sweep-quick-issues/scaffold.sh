#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own, as
# owner/name. Nothing here can be faked locally: the point of the case is real
# issues on a real tracker, and a sweep that opens real pull requests. The
# scaffold clones that repo, writes a tiny project with one real test, a Checks
# block and a README, pushes one commit, and opens four issues.
#
# It does NOT use fixtures/greeter.sh: that fixture inits its own git repo and
# remote, which cannot be done inside a clone. The layout is copied from
# plans-on-tracker's scaffold.
#
# Everything goes through `gh api`, never `gh issue`: the issue commands send
# GraphQL, which a cloud session's proxy refuses.
#
# THE FOUR ISSUES, and what each one is for:
#   1 and 2  both change src/greet.js, so `sweep` must put them in ONE chain,
#            one sweeper, one PR that closes both.
#   3        changes README.md only, so it is a chain of its own: a second PR.
#   4        is not Quick (a design choice across many files with no nameable
#            file), so `sweep` must skip it and start nothing for it.
# Three Quick issues in two chains is the shape the graders count.
workspace="${1:-$PWD}"

: "${DEVFLOW_EVAL_REPO:?set DEVFLOW_EVAL_REPO=owner/name to a throwaway repo you own}"

gh repo clone "$DEVFLOW_EVAL_REPO" "$workspace" -- -q
cd "$workspace"

mkdir -p src test
cat > package.json <<'JSON'
{ "name": "greeter", "version": "1.0.0", "private": true,
  "scripts": { "test": "node --test" } }
JSON
cat > src/greet.js <<'JS'
module.exports = (name) => `hello ${name}`;
JS
cat > test/greet.test.js <<'JS'
const test = require("node:test");
const assert = require("node:assert");
const greet = require("../src/greet");
test("greets by name", () => assert.ok(greet("Eddie").toLowerCase().includes("eddie")));
JS
cat > README.md <<'MD'
# greeter

Say hello to teh person you name.
MD
cat > CLAUDE.md <<'MD'
## Checks
- Test: npm test
MD

npm test >/dev/null 2>&1 \
  || { echo "scaffold.sh: npm test does not pass on the fresh fixture" >&2; exit 1; }

# Safe to run again: commit only if something changed, and set the upstream so
# a freshly created empty repo works too.
git add -A
git diff --cached --quiet || git commit -qm "chore: greeter fixture for the sweep case"
git push -q -u origin HEAD

LABEL="devflow:eval-sweep"
gh api "repos/$DEVFLOW_EVAL_REPO/labels" -f name="$LABEL" -f color=BFD4F2 \
  -f description="Opened by the sweep-quick-issues eval" >/dev/null 2>&1 || true

# Leave no state from a previous run. A leftover open issue would be swept too.
# Only the issues this scaffold opened carry the label, and pull requests that
# a past run opened are for the human to close by hand.
gh api --paginate "repos/$DEVFLOW_EVAL_REPO/issues?labels=$LABEL&state=open&per_page=100" \
  --jq '.[] | select(.pull_request | not) | .number' \
  | while read -r n; do
      [ -n "$n" ] && gh api -X PATCH "repos/$DEVFLOW_EVAL_REPO/issues/$n" -f state=closed >/dev/null || true
    done

# Prints the new issue's number.
open_issue() {
  gh api "repos/$DEVFLOW_EVAL_REPO/issues" -f title="$1" -f body="$2" \
    -f "labels[]=$LABEL" --jq .number
}

NUMBERS="$(
open_issue "Make greet() end with an exclamation mark" \
  "greet() in src/greet.js should end with an exclamation mark, so greet('Eddie') returns 'hello Eddie!'. Update the test in test/greet.test.js if it needs it."
open_issue "Make greet() capitalise the name" \
  "greet() in src/greet.js should capitalise the first letter of the name it is given, so greet('eddie') includes 'Eddie'."
open_issue "Fix the typo in the README" \
  "README.md says 'teh person'. It should say 'the person'."
open_issue "Rework the greeting across every module" \
  "The greeting should be configurable per user, per language and per channel. That means a config file, a command line, and changes through all of the modules. I have not decided the shape yet, so it needs working out first."
)"

# The prompt names this file, so the run sweeps these four and never the real
# issues a repo may also have. Excluded from git so it does not dirty the tree.
echo "$NUMBERS" | tr '\n' ' ' > .sweep-issues
echo ".sweep-issues" >> .git/info/exclude

[ "$(wc -w < .sweep-issues | tr -d ' ')" = "4" ] \
  || { echo "scaffold.sh: expected 4 issue numbers, got: $(cat .sweep-issues)" >&2; exit 1; }

echo "scaffold.sh: opened issues $(cat .sweep-issues) in $DEVFLOW_EVAL_REPO"
