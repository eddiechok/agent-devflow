#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# No --with-checks-block: writing that file is what this case measures.
# The project has a test and a lint command and deliberately no typecheck,
# so the case can also check that setup does not invent the missing one.
# The fixture asserts CLAUDE.md is absent before returning.
"$here/../fixtures/greeter.sh" "$workspace"
