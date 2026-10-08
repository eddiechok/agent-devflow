#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# One module with two callers inside this repo. Nothing here is on flow's own
# danger list: no auth, no secrets, no payments, no public API anyone outside
# depends on. Only the project's CLAUDE.md says it is dangerous.
mkdir -p src/shared

cat > src/shared/format.js <<'JS'
export function displayName(name) {
  return name;
}
JS

cat > src/greet.js <<'JS'
import { displayName } from "./shared/format.js";

export function greet(name) {
  if (!name) throw new Error("name is required");
  return `Hello, ${displayName(name)}!`;
}
JS

cat > src/badge.js <<'JS'
import { displayName } from "./shared/format.js";

export function badge(name) {
  return `[ ${displayName(name).toUpperCase()} ]`;
}
JS

# Worded the way a real repo writes it: bykare-medusa-admin's CLAUDE.md has a
# "Danger list" section of its own, and that is the shape under test.
cat >> CLAUDE.md <<'MD'

## Danger list

Escalate, never fast-path:
- `src/shared/` — imported by both the greeter and the badge printer. A change
  here can silently break one of them. Check both.
MD

git add -A
git commit -qm "feat: shared display name, used by greet and badge"
# Pushed, so main has nothing ahead. Unpushed, all three first runs spent turns
# hunting for a pull request the one commit might belong to.
git push -q


fail() { echo "scaffold.sh: $1" >&2; exit 1; }
npm test >/dev/null 2>&1 || fail "npm test does not pass after the shared module"
grep -q '^## Danger list' CLAUDE.md || fail "CLAUDE.md has no Danger list"
[ -z "$(git status --porcelain)" ] || fail "working tree dirty after committing"
[ "$(git rev-list --count origin/main..main)" = "0" ] || fail "main is ahead of origin"
