#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# A direct project. The shared fixture writes a `## Workflow` block saying pr;
# swap its lines rather than add a second block, which a skill reading the first
# one would take as pr. Through a temp file because `sed -i` differs between
# BSD and GNU sed.
tmp="$(mktemp)"
sed -e 's/^- Mode: pr$/- Mode: direct/' \
    -e 's/^- About: .*/- About: a tiny CLI that says hello/' CLAUDE.md > "$tmp" \
  && mv "$tmp" CLAUDE.md

# No remote. The fixture adds a bare one so submit can push in the other cases;
# a direct project with nowhere to push is the path this case measures, where
# the work is committed and the run says it did not push. Removing the remote
# removes the upstream and the tracking branch with it.
git remote remove origin

# The same typo as sizing-quick, written through a temp file because `sed -i`
# differs between BSD and GNU sed.
tmp="$(mktemp)"
sed 's/says hello/sasy hello/' README.md > "$tmp" && mv "$tmp" README.md
grep -q "sasy hello" README.md || {
  echo "scaffold.sh: the typo was not introduced -- the fixture README changed shape" >&2
  exit 1
}

git add -A
git commit -qm "docs: readme"

[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree dirty after committing the fixture" >&2
  exit 1
}
[ -z "$(git remote)" ] || {
  echo "scaffold.sh: a remote is still set, so the project is not remote-less" >&2
  exit 1
}
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || {
  echo "scaffold.sh: not on main" >&2
  exit 1
}
grep -q '^- Mode: direct$' CLAUDE.md || {
  echo "scaffold.sh: CLAUDE.md does not say Mode: direct" >&2
  exit 1
}
