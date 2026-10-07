#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# The shared fixture gives the repo a package.json, code and a clean commit on
# main. The one thing this case adds is the file signal: a railway.json is what
# the vendor table keys the Railway row to.
"$here/../fixtures/greeter.sh" "$workspace"

cd "$workspace"

cat > railway.json <<'JSON'
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": { "startCommand": "node src/cli.js" }
}
JSON

git add railway.json
git commit -qm "chore: deploy on railway"
git push -q origin main

# Same self-check the shared fixture makes: a fixture that comes out wrong
# reads as the plugin failing.
[ -f railway.json ] || { echo "scaffold.sh: railway.json is missing" >&2; exit 1; }
[ -f package.json ] || { echo "scaffold.sh: package.json is missing" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "scaffold.sh: tree is dirty" >&2; exit 1; }
