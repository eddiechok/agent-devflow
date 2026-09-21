#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# With the Checks block, since this case starts where setup left off.
# origin/HEAD stays unset (see fixtures/greeter.sh) -- that is the state that
# broke default-branch detection, and the fixture asserts it stayed unset.
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
