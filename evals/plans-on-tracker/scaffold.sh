#!/usr/bin/env bash
set -euo pipefail

# MANUAL case. Set DEVFLOW_EVAL_REPO to a throwaway GitHub repo you own,
# as owner/name. The scaffold clones it and writes a CLAUDE.md that keeps
# plans on GitHub. Nothing here can be faked locally: the point of the case
# is a real issue on a real tracker.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

: "${DEVFLOW_EVAL_REPO:?set DEVFLOW_EVAL_REPO=owner/name to a throwaway repo you own}"

gh repo clone "$DEVFLOW_EVAL_REPO" "$workspace" -- -q
cd "$workspace"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cat >> CLAUDE.md <<'BLOCK'

## Plans
- Tracker: github
BLOCK

gh label create devflow:plan --description "A devflow Deep plan" --color 0E8A16 2>/dev/null || true

git add -A
git commit -qm "chore: greeter fixture with plans on github"
git push -q
