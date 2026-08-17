#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# With the Checks block, since this case starts where setup left off.
# origin/HEAD stays unset (see fixtures/greeter.sh) -- that is the state that
# broke default-branch detection, so leaving it unset is the regression test.
"$here/../fixtures/greeter.sh" "$PWD" --with-checks-block
