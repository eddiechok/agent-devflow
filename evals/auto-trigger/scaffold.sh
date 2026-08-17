#!/usr/bin/env bash
set -euo pipefail

# $0 rather than BASH_SOURCE, which is empty if the runner invokes this with
# `sh scaffold.sh` rather than executing it. The workspace may arrive as an
# argument or as the current directory; take whichever is offered.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# Nothing to mutate: the fixture README already carries the dry line the case
# asks about. Assert it is there anyway, so a change to the shared fixture
# fails here, naming the reason, rather than showing up as an unexplained red
# in the graders.
grep -q "A tiny CLI that says hello." README.md || {
  echo "scaffold.sh: the README description line is gone -- the shared fixture" >&2
  echo "  changed shape, so this case is no longer asking about anything." >&2
  exit 1
}

# The prompt must be a request, not a reaction to a diff already on disk. A
# dirty tree would also let `flow` reach step 5 with work it did not do.
[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree is dirty before the run" >&2
  exit 1
}
