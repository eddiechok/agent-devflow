#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own, as
# owner/name. Nothing here can be faked locally: the point of the case is real
# issues on a real tracker. The scaffold clones that repo, writes a tiny
# project with one real test, a Checks block and a README, and pushes one
# commit. It opens no issue: scout opens them.
#
# It does NOT use fixtures/greeter.sh: that fixture inits its own git repo and
# remote, which cannot be done inside a clone. The layout is copied from
# sweep-quick-issues' scaffold.
#
# Everything goes through `gh api`, never `gh issue`: the issue commands send
# GraphQL, which a cloud session's proxy refuses.
#
# THE TWO PLANTED THINGS, and what each one is for:
#   lastN      in src/stats.js. lastN(list, 0) returns the whole list, because
#              slice(-0) is slice(0). A real bug, found by reading, and not
#              covered by the tests. Scout must file it.
#   readCache  in src/cache.js. It swallows its error on purpose: a cache miss
#              only means the value is computed again. A comment and the README
#              say so. A careless audit flags an empty catch; scout must not.
workspace="${1:-$PWD}"

: "${DEVFLOW_EVAL_REPO:?set DEVFLOW_EVAL_REPO=owner/name to a throwaway repo you own}"

# Scout never files a fingerprint twice, open or closed (closed means turned
# down). So a repo with scout's issues from a past run would make this run file
# nothing, and the case would fail for the wrong reason. Stop and say so.
if gh api --paginate "repos/$DEVFLOW_EVAL_REPO/issues?state=all&per_page=100" \
     --jq '.[] | select(.body // "" | contains("devflow:scout")) | .number' | grep -q .; then
  echo "scaffold.sh: $DEVFLOW_EVAL_REPO already has a devflow:scout issue. Use a fresh repo." >&2
  exit 1
fi

gh repo clone "$DEVFLOW_EVAL_REPO" "$workspace" -- -q
cd "$workspace"

mkdir -p src test
cat > package.json <<'JSON'
{ "name": "stats-kit", "version": "1.0.0", "private": true,
  "scripts": { "test": "node --test" } }
JSON
cat > src/stats.js <<'JS'
// Small helpers over lists of numbers.
const sum = (list) => list.reduce((a, b) => a + b, 0);

// The last n items of the list.
const lastN = (list, n) => list.slice(-n);

module.exports = { sum, lastN };
JS
cat > src/cache.js <<'JS'
const fs = require("node:fs");

// Reads a cached value from disk. A failed read is swallowed by design: a
// miss only means the caller computes the value again, and the cache must
// never be the reason a request fails.
function readCache(path) {
  try {
    return JSON.parse(fs.readFileSync(path, "utf8"));
  } catch (e) {
    return null;
  }
}

module.exports = { readCache };
JS
cat > test/stats.test.js <<'JS'
const test = require("node:test");
const assert = require("node:assert");
const { sum, lastN } = require("../src/stats");
test("sums a list", () => assert.strictEqual(sum([1, 2, 3]), 6));
test("takes the last two", () => assert.deepStrictEqual(lastN([1, 2, 3], 2), [2, 3]));
JS
cat > README.md <<'MD'
# stats-kit

Small helpers over lists of numbers, and a disk cache.

Cache reads never throw: a failed read returns null on purpose, so the caller
computes the value again.
MD
cat > CLAUDE.md <<'MD'
## Checks
- Test: npm test

## Workflow
- Mode: pr
- About: a tiny stats library, used by devflow's evals
MD

npm test >/dev/null 2>&1 \
  || { echo "scaffold.sh: npm test does not pass on the fresh fixture" >&2; exit 1; }

# Safe to run again: commit only if something changed, and set the upstream so
# a freshly created empty repo works too.
git add -A
git diff --cached --quiet || git commit -qm "chore: stats-kit fixture for the scout case"
git push -q -u origin HEAD

echo "scaffold.sh: planted lastN and readCache in $DEVFLOW_EVAL_REPO"
