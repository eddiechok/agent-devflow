#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own, as
# owner/name. Nothing here can be faked locally: the point of the case is real
# issues on a real tracker. The scaffold clones that repo, writes a tiny project
# with one real test, a Checks block and a README, pushes one commit, and opens
# five issues. Unlike sweep-quick-issues, the run opens no pull requests: with no
# session tool in `claude -p`, `dispatch` only prints.
#
# It does NOT use fixtures/greeter.sh: that fixture inits its own git repo and
# remote, which cannot be done inside a clone. The layout is copied from
# sweep-quick-issues' scaffold.
#
# Everything goes through `gh api`, never `gh issue`: the issue commands send
# GraphQL, which a cloud session's proxy refuses.
#
# THE FIVE ISSUES, oldest first, and what each one is for:
#   1  Standard feature. Not a bug and nothing waits on it, so it ranks by age:
#      the second pick.
#   2  Deep feature (no nameable file yet). Also ranks by age: the third pick.
#   3  A bug nobody can point at, labelled `bug`. That is Standard, and bugs
#      rank before age: the first pick, although it is the third oldest.
#   4  Standard, but the newest of those that stay: the fourth, so `dispatch`
#      must skip it as not in the top 3.
#   5  A README typo. Quick: `dispatch` must skip it and point at /devflow:sweep.
# Three picks and two skips is the shape the graders count. No issue names
# another, so none is blocked and none ranks by what it unblocks.
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

## Workflow
- Mode: pr
- About: a tiny CLI that says hello, used by devflow's evals
MD

npm test >/dev/null 2>&1 \
  || { echo "scaffold.sh: npm test does not pass on the fresh fixture" >&2; exit 1; }

# Safe to run again: commit only if something changed, and set the upstream so
# a freshly created empty repo works too.
git add -A
git diff --cached --quiet || git commit -qm "chore: greeter fixture for the dispatch case"
git push -q -u origin HEAD

LABEL="devflow:eval-dispatch"
gh api "repos/$DEVFLOW_EVAL_REPO/labels" -f name="$LABEL" -f color=BFD4F2 \
  -f description="Opened by the dispatch-top-three eval" >/dev/null 2>&1 || true

# Leave no state from a previous run. A leftover open issue would be ranked too.
# Only the issues this scaffold opened carry the label.
gh api --paginate "repos/$DEVFLOW_EVAL_REPO/issues?labels=$LABEL&state=open&per_page=100" \
  --jq '.[] | select(.pull_request | not) | .number' \
  | while read -r n; do
      [ -n "$n" ] && gh api -X PATCH "repos/$DEVFLOW_EVAL_REPO/issues/$n" -f state=closed >/dev/null || true
    done

# Prints the new issue's number. The third argument is a second label, or "-".
# The pause keeps created_at distinct, because "oldest" is what ranks three of
# the five.
open_issue() {
  local extra="${3:--}"
  if [ "$extra" = "-" ]; then
    gh api "repos/$DEVFLOW_EVAL_REPO/issues" -f title="$1" -f body="$2" \
      -f "labels[]=$LABEL" --jq .number
  else
    gh api "repos/$DEVFLOW_EVAL_REPO/issues" -f title="$1" -f body="$2" \
      -f "labels[]=$LABEL" -f "labels[]=$extra" --jq .number
  fi
  sleep 2
}

NUMBERS="$(
open_issue "Let greet() take a greeting word" \
  "greet(name, word) should use word in place of 'hello' and default to 'hello', so greet('Eddie', 'hi') returns 'hi Eddie'. It changes greet() in src/greet.js and its test in test/greet.test.js."
open_issue "Make the greeting configurable per user, language and channel" \
  "The greeting should be configurable per user, per language and per channel. That means a config file, a command line, and changes through all of the modules. I have not decided the shape yet, so it needs working out first."
open_issue "greet() sometimes says hello undefined" \
  "A few users report a greeting that reads 'hello undefined'. I cannot reproduce it and I do not know where the missing name comes from. It needs finding first." bug
open_issue "Tidy the name greet() is given" \
  "greet() should trim the name and collapse runs of spaces inside it, and return 'hello there' when the name is empty after that. Update the tests in test/greet.test.js."
open_issue "Fix the typo in the README" \
  "README.md says 'teh person'. It should say 'the person'."
)"

# The prompt names this file, so the run ranks these five and never the real
# issues a repo may also have. Excluded from git so it does not dirty the tree.
echo "$NUMBERS" | tr '\n' ' ' > .dispatch-issues
echo ".dispatch-issues" >> .git/info/exclude

[ "$(wc -w < .dispatch-issues | tr -d ' ')" = "5" ] \
  || { echo "scaffold.sh: expected 5 issue numbers, got: $(cat .dispatch-issues)" >&2; exit 1; }

echo "scaffold.sh: opened issues $(cat .dispatch-issues) in $DEVFLOW_EVAL_REPO"
