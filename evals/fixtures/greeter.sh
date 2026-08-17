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
set -euo pipefail

target="${1:?usage: greeter.sh <target-dir> [--with-checks-block]}"
with_checks="${2:-}"

mkdir -p "$target/src" "$target/test"
cd "$target"

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

# A real remote, so `ship` can push and reach its PR step the way it would in
# a real repo. A bare repo is enough -- the PR call itself will fail without a
# GitHub host, and how devflow reports that failure is worth seeing.
#
# mktemp, not a path beside $target: two cases whose workspaces share a parent
# would otherwise scaffold onto the same bare repo, and the second push fails
# as a non-fast-forward. Keeping it out of the work tree also stops `ship`
# from picking the bare repo up as project files.
origin="$(mktemp -d)/greeter-origin.git"
git init -q -b main
git add -A
git -c user.email=eval@example.com -c user.name=eval commit -qm "feat: greeter cli"
git init -q --bare "$origin"
git remote add origin "$origin"
git push -q -u origin main

# Deliberately left unset: origin/HEAD. That is the normal state of a fresh
# clone, and it is what broke the default-branch detection in flow and ship.
