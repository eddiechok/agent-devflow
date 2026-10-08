#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

# A small web app with one list page. The seeded data is never empty, so the
# empty state is a page the run has to make: the project's CLAUDE.md says how.
# The server appends each page it serves to served.log. That file is what the
# graders read: a test or an edit the run writes cannot contain it, so only a
# page actually served empty can. Not the trace: a browser check reads only the
# element the change touched, so the page's HTML never reaches it.
mkdir -p src test data
printf 'served.log\n' >> .gitignore

cat > src/orders.js <<'JS'
export const EMPTY_TEXT = "Nothing here yet.";

export function renderOrders(orders) {
  if (orders.length === 0) {
    return `<p data-state="empty">${EMPTY_TEXT}</p>`;
  }
  const rows = orders.map((o) => `<li>#${o.id} ${o.item}</li>`).join("");
  return `<ul>${rows}</ul>`;
}
JS

cat > src/server.js <<'JS'
import http from "node:http";
import fs from "node:fs";
import { renderOrders } from "./orders.js";

const file = process.env.ORDERS_FILE ?? "data/orders.json";
const port = Number(process.env.PORT ?? 4100);

http
  .createServer((req, res) => {
    if (req.url !== "/orders") {
      res.writeHead(404).end("not found");
      return;
    }
    const orders = JSON.parse(fs.readFileSync(file, "utf8"));
    const list = renderOrders(orders);
    fs.appendFileSync("served.log", `rendered ${orders.length} orders from ${file}: ${list}\n`);
    res.writeHead(200, { "content-type": "text/html" });
    res.end(
      `<!doctype html><title>Orders</title><h1>Orders</h1>\n` +
        `${list}\n` +
        `<!-- rendered ${orders.length} orders from ${file} -->\n`,
    );
  })
  .listen(port, () => console.log(`orders on http://localhost:${port}/orders`));
JS

cat > data/orders.json <<'JSON'
[
  { "id": 1001, "item": "Walnut desk" },
  { "id": 1002, "item": "Desk lamp" },
  { "id": 1003, "item": "Chair" }
]
JSON

printf '[]\n' > data/empty.json

cat > test/orders.test.js <<'JS'
import { test } from "node:test";
import assert from "node:assert/strict";
import { renderOrders } from "../src/orders.js";

test("lists each order", () => {
  const html = renderOrders([{ id: 1001, item: "Walnut desk" }]);
  assert.equal(html, "<ul><li>#1001 Walnut desk</li></ul>");
});
JS

# Worded the way a real repo writes it: the login, URLs and traps of a project
# live in its own CLAUDE.md. `- Driver: session` means the check uses whatever
# driver the session has; with no `## Browser` block at all, flow would ask the
# driver question first (#129) and this case would grade that instead.
cat >> CLAUDE.md <<'MD'

## Browser
- Driver: session

## Running the app

- Start it: `PORT=4100 node src/server.js`, then open http://localhost:4100/orders
- No login. The list is seeded with three orders from `data/orders.json`.
- The list is empty only when started with `ORDERS_FILE=data/empty.json`.
  Stop the server and start it again with that to see the empty state.
MD

git add -A
git commit -qm "feat: orders page with an empty state"
git push -q

fail() { echo "scaffold.sh: $1" >&2; exit 1; }
if [ -f package.json ]; then
  npm test >/dev/null 2>&1 || fail "npm test does not pass after the orders page"
fi
grep -q 'ORDERS_FILE=data/empty.json' CLAUDE.md || fail "CLAUDE.md does not say how to empty the list"
[ -z "$(git status --porcelain)" ] || fail "working tree dirty after committing"
[ "$(git rev-list --count origin/main..main)" = "0" ] || fail "main is ahead of origin"
