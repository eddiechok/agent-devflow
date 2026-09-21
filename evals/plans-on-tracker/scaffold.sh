#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own, as
# owner/name. Nothing here can be faked locally: the point of the case is a
# real issue on a real tracker. The scaffold clones that repo, writes a tiny
# project with one real test, a Checks block and a Plans block, and pushes
# one commit. It does NOT use fixtures/greeter.sh: that fixture inits its own
# git repo and remote, which cannot be done inside a clone.
here="$(cd "$(dirname "$0")" && pwd)"
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
test("greets by name", () => assert.strictEqual(greet("Eddie"), "hello Eddie"));
JS
cat > CLAUDE.md <<'MD'
## Checks
- Test: npm test

## Plans
- Tracker: github
MD

npm test >/dev/null 2>&1 || { echo "scaffold.sh: npm test does not pass on the fresh fixture" >&2; exit 1; }
gh label create devflow:plan --description "A devflow Deep plan" --color 0E8A16 2>/dev/null || true

git add -A
git commit -qm "chore: greeter fixture with plans on github"
git push -q
