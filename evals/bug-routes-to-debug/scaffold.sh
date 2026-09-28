#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# A real bug, with no test guarding it and nothing naming it: batch mode calls
# countGreeting() twice per name, so the printed count runs ahead of the name
# list and the gap widens with every name. Nothing here says so in a comment
# or a failing test -- finding that is devflow:debug's job, not something the
# request or the fixture hands over.
cat > src/counter.js <<'JS'
let seen = 0;

export function countGreeting() {
  seen += 1;
  return seen;
}
JS

cat > src/cli.js <<'JS'
#!/usr/bin/env node
import { greet } from "./greet.js";
import { countGreeting } from "./counter.js";

const args = process.argv.slice(2);

if (args[0] === "--batch") {
  for (const name of args.slice(1)) {
    const n = countGreeting();
    console.log(`${greet(name)} (#${n})`);
    countGreeting();
  }
} else {
  const name = args[0] ?? "world";
  console.log(greet(name));
}
JS

git add -A
git commit -qm "feat: batch mode with a running count"

fail() { echo "scaffold.sh: fixture is broken -- $1" >&2; exit 1; }

# The existing suite never touches batch mode, so it still passes -- there is
# no red test pointing at the bug, which is the point of this fixture.
npm test >/dev/null 2>&1 || fail "npm test no longer passes after adding batch mode"

out="$(node src/cli.js --batch alice bob carol)"
echo "$out" | grep -q '(#1)' || fail "batch mode did not print the expected first count"
echo "$out" | grep -q '(#3)' || fail "the double-count bug did not reproduce on the second name"
echo "$out" | grep -q '(#5)' || fail "the double-count bug did not reproduce on the third name"

[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree dirty after committing batch mode" >&2
  exit 1
}
