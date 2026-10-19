#!/bin/sh
# The Deploy line: update devflow's local-scope install from the main checkout.
#
#     sh scripts/deploy.sh
#
# A local-scope install is one entry per folder, keyed to the folder the update
# runs in. Run from a worktree, the update changes only that worktree's entry
# and still says it updated, so this goes to the main checkout first. A merge to
# main changes nothing a session sees until this runs and the session restarts.
set -e
cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
claude plugin update devflow@eddiechok-devflow --scope local
echo "Restart the session to load the new version."
