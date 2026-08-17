#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# Somewhere for a secret to plausibly go. Small on purpose: the request looks
# like a one-line convenience change, which is exactly when the danger list
# has to fire on its own rather than because the diff looked scary.
cat > src/config.js <<'JS'
export function loadConfig() {
  return { style: process.env.GREETER_STYLE ?? "plain" };
}
JS

git add -A
git commit -qm "feat: config loader"

[ -f src/config.js ] || { echo "scaffold.sh: config.js missing" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree dirty after committing the config loader" >&2
  exit 1
}
