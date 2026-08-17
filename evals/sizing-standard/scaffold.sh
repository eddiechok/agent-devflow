#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# With the Checks block: this case starts where setup left off, and the size
# call should not depend on whether the project is configured yet.
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
