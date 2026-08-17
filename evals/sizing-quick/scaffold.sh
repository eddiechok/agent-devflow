#!/usr/bin/env bash
set -euo pipefail

# $0 rather than BASH_SOURCE, which is empty if the runner invokes this with
# `sh scaffold.sh` rather than executing it. The workspace may arrive as an
# argument or as the current directory; take whichever is offered.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# The typo the case asks about. Committed, so the working tree starts clean
# and `flow` is sizing a request rather than reacting to a dirty diff.
#
# Written through a temp file because `sed -i` takes an argument on BSD sed
# and does not on GNU sed, and these run on whatever laptop you have.
tmp="$(mktemp)"
sed 's/says hello/sasy hello/' README.md > "$tmp" && mv "$tmp" README.md
grep -q "sasy hello" README.md || {
  echo "scaffold.sh: the typo was not introduced -- the fixture README changed shape" >&2
  exit 1
}

git commit -aqm "docs: readme"
[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree dirty after committing the typo" >&2
  exit 1
}
