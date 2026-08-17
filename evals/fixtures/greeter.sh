#!/usr/bin/env bash
# Shared fixture: a tiny Node CLI with real, working check commands.
#
# Real commands matter more than they look. Half of what these evals assert is
# that devflow runs the project's declared commands rather than a substitute,
# and you cannot catch a substitution against a project whose checks are fake.
#
# Usage: greeter.sh <target-dir> [--with-checks-block]
#
#   --with-checks-block   also write the CLAUDE.md that `setup` would have
#                         written. Omit it when the case is testing `setup`
#                         itself.
#
# Defensive throughout, because the runner's invocation contract is not
# something this repo can verify: which directory it makes current, whether it
# passes the workspace as an argument, and whether it runs the script with
# bash or sh are all assumptions. Everything below either holds under any of
# those, or fails loudly saying which one broke.
set -euo pipefail

target="${1:?usage: greeter.sh <target-dir> [--with-checks-block]}"
with_checks="${2:-}"

mkdir -p "$target"
target="$(cd "$target" && pwd)"

# --------------------------------------------------------------- safety rails

# The failure that would actually hurt: if the runner makes the case directory
# current instead of a scratch workspace, `$PWD` is inside this repo and the
# lines below would git-init a fixture on top of the plugin's own source.
# Refuse rather than find out afterwards.
probe="$target"
while [ "$probe" != "/" ]; do
  if [ -f "$probe/.claude-plugin/plugin.json" ] || [ -f "$probe/plugin.json" ]; then
    echo "greeter.sh: refusing to scaffold into $target" >&2
    echo "  it sits inside a plugin checkout ($probe)." >&2
    echo "  The runner made a directory current that is not a scratch" >&2
    echo "  workspace. Scaffolding here would write over real source." >&2
    exit 1
  fi
  probe="$(dirname "$probe")"
done

for leftover in case.yaml scaffold.sh; do
  if [ -e "$target/$leftover" ]; then
    echo "greeter.sh: refusing to scaffold into $target" >&2
    echo "  it already contains $leftover, so it is an eval case directory" >&2
    echo "  rather than a workspace." >&2
    exit 1
  fi
done

cd "$target"

# ------------------------------------------------------------------ the files

mkdir -p src test

cat > package.json <<'JSON'
{
  "name": "greeter",
  "version": "0.1.0",
  "type": "module",
  "bin": { "greeter": "./src/cli.js" },
  "scripts": {
    "test": "node --test",
    "lint": "node --check src/greet.js && node --check src/cli.js"
  }
}
JSON

cat > src/greet.js <<'JS'
export function greet(name) {
  if (!name) throw new Error("name is required");
  return `Hello, ${name}!`;
}
JS

cat > src/cli.js <<'JS'
#!/usr/bin/env node
import { greet } from "./greet.js";

const name = process.argv[2] ?? "world";
console.log(greet(name));
JS

cat > test/greet.test.js <<'JS'
import { test } from "node:test";
import assert from "node:assert/strict";
import { greet } from "../src/greet.js";

test("greets a name", () => {
  assert.equal(greet("Eddie"), "Hello, Eddie!");
});

test("rejects an empty name", () => {
  assert.throws(() => greet(""), /name is required/);
});
JS

cat > README.md <<'MD'
# greeter

A tiny CLI that says hello.

```bash
node src/cli.js Eddie
# Hello, Eddie!
```
MD

printf 'node_modules/\n' > .gitignore

if [ "$with_checks" = "--with-checks-block" ]; then
  cat > CLAUDE.md <<'MD'
## Checks
- Test: npm test
- Lint: npm run lint
MD
fi

# -------------------------------------------------------------------- the git

git init -q -b main

# Set locally rather than relying on the sandbox having a global identity, and
# turn signing off. `submit` commits during the run, and a missing user.email or
# a signing prompt would fail the case for a reason that has nothing to do
# with devflow.
git config user.email "eval@example.com"
git config user.name "eval"
git config commit.gpgsign false

git add -A
git commit -qm "feat: greeter cli"

# A real remote, so `submit` can push and reach its PR step the way it would in
# a real repo. A bare repo is enough -- the PR call itself will fail without a
# GitHub host, and how devflow reports that failure is worth seeing.
#
# mktemp, not a path beside $target: two cases whose workspaces share a parent
# would otherwise scaffold onto the same bare repo, and the second push fails
# as a non-fast-forward. Keeping it out of the work tree also stops `submit`
# from picking the bare repo up as project files.
origin="$(mktemp -d)/greeter-origin.git"
git init -q --bare "$origin"
git remote add origin "$origin"
git push -q -u origin main

# Deliberately left unset: origin/HEAD. That is the normal state of a fresh
# clone, and it is what broke the default-branch detection in flow and submit.

# ------------------------------------------------------------ self-verification

# A fixture that quietly comes out wrong reads as the plugin failing. Prove the
# things every case depends on, here, where the error message can say which one
# broke.
fail() { echo "greeter.sh: fixture is broken -- $1" >&2; exit 1; }

npm test  >/dev/null 2>&1 || fail "npm test does not pass on the fresh fixture"
npm run lint >/dev/null 2>&1 || fail "npm run lint does not pass on the fresh fixture"
node src/cli.js Eddie >/dev/null 2>&1 || fail "the CLI does not run"
[ -z "$(git status --porcelain)" ] || fail "working tree is dirty after scaffolding"
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || fail "not on main"
git rev-parse --abbrev-ref '@{upstream}' >/dev/null 2>&1 || fail "no upstream tracking branch"
git symbolic-ref --short refs/remotes/origin/HEAD >/dev/null 2>&1 \
  && fail "origin/HEAD is set, which defeats the default-branch regression test"

if [ "$with_checks" = "--with-checks-block" ]; then
  [ -f CLAUDE.md ] || fail "CLAUDE.md was requested but is missing"
else
  [ ! -f CLAUDE.md ] || fail "CLAUDE.md exists but this case tests setup writing it"
fi

echo "greeter.sh: scaffolded and verified in $target"
