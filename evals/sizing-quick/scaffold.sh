#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$here/../fixtures/greeter.sh" "$PWD" --with-checks-block

# The typo the case asks about. Committed, so the working tree starts clean
# and `flow` is sizing a request rather than reacting to a dirty diff.
sed -i 's/says hello/sasy hello/' README.md
git -c user.email=eval@example.com -c user.name=eval commit -aqm "docs: readme"
