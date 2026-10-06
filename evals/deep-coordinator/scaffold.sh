#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# With the Checks block, since this case starts where setup left off.
# origin/HEAD stays unset (see fixtures/greeter.sh) -- that is the state that
# broke default-branch detection, and the fixture asserts it stayed unset.
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block

# plan starts parallel chains only when worktree.baseRef is already "head"
# when the session starts. A setting it writes itself takes effect next
# session, so without this the run builds one chain at a time and never
# merges (#112). Excluded from git, so the tree stays clean.
mkdir -p "$workspace/.claude"
printf '{"worktree": {"baseRef": "head"}}\n' > "$workspace/.claude/settings.local.json"
printf '.claude/settings.local.json\n' >> "$workspace/.git/info/exclude"
