#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# A real bug that reading cannot find. --batch-file greets each unique name
# once, through a Set of trimmed lines, and that code is correct. The fault is
# in the data: the second "alice" in team.txt ends in a zero-width space,
# which trim() does not strip and which prints as nothing. So alice is greeted
# twice, the file looks right on screen, and the code looks right. Running it
# and looking at the bytes shows the cause -- devflow:debug's job. A model that
# reads team.txt does receive the character, which is this case's known limit
# (see case.yaml). Nothing here names it in a comment the session would see,
# or in a failing test.
cat > src/cli.js <<'JS'
#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { greet } from "./greet.js";

const args = process.argv.slice(2);

if (args[0] === "--batch-file") {
  const lines = readFileSync(args[1], "utf8").split("\n");
  const names = new Set(lines.map((line) => line.trim()).filter(Boolean));
  for (const name of names) {
    console.log(greet(name));
  }
} else {
  const name = args[0] ?? "world";
  console.log(greet(name));
}
JS

printf 'alice\nbob\ncarol\nalice\xe2\x80\x8b\n' > team.txt

git add -A
git commit -qm "feat: greet everyone in a team file, once each"

fail() { echo "scaffold.sh: fixture is broken -- $1" >&2; exit 1; }

npm test >/dev/null 2>&1 || fail "npm test no longer passes after adding --batch-file"

out="$(node src/cli.js --batch-file team.txt)"
[ "$(echo "$out" | grep -c '^Hello, alice')" = "2" ] || fail "alice is not greeted twice, so the bug did not reproduce"
[ "$(echo "$out" | wc -l | tr -d ' ')" = "4" ] || fail "expected four greetings, one of them the duplicate"
[ "$(grep -c '^alice$' team.txt)" = "1" ] || fail "the duplicate alice is visible as a plain line, so reading would find it"

[ -z "$(git status --porcelain)" ] || {
  echo "scaffold.sh: working tree dirty after committing --batch-file" >&2
  exit 1
}
