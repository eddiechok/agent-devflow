#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# No --with-checks-block: writing that file is what this case measures.
# The project has a test and a lint command and deliberately no typecheck,
# so the case can also check that setup does not invent the missing one.
"$here/../fixtures/greeter.sh" "$PWD"
