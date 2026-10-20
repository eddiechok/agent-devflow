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
# A worktree cut before a deploy fix carries the old scripts, so a copy that is
# not the main checkout's hands over to it; that copy runs on with no re-exec.
set -e
here="$(cd "$(dirname "$0")" && pwd -P)"
cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
main_copy="$(pwd -P)/scripts/deploy.sh"
[ "$here/$(basename "$0")" = "$main_copy" ] || exec sh "$main_copy"
claude plugin update devflow@eddiechok-devflow --scope local
python3 "$here/prune-install.py"
echo "Restart the session to load the new version."
