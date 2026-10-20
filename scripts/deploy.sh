#!/bin/sh
# The Deploy line: update devflow's local-scope install from the main checkout.
#
#     sh scripts/deploy.sh
#
# A local-scope install is one entry per folder, keyed to the folder the update
# runs in. Run from a worktree, the update changes only that worktree's entry
# and still says it updated, so this goes to the main checkout first. A merge to
# main changes nothing a session sees until this runs and the session restarts.
# The update copies untracked files too, so prune-install.py drops them after.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
claude plugin update devflow@eddiechok-devflow --scope local
python3 "$here/prune-install.py"
echo "Restart the session to load the new version."
