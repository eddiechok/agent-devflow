#!/usr/bin/env bash
set -euo pipefail

# See sizing-quick/scaffold.sh for why $0 and the optional argument.
here="$(cd "$(dirname "$0")" && pwd)"
workspace="${1:-$PWD}"

# The shared fixture gives the repo a CLI, its checks block and a clean commit on
# main with a remote. This case adds the one thing it lacks: a UI, so a decision
# about how a new page should look has something to be about.
"$here/../fixtures/greeter.sh" "$workspace" --with-checks-block
cd "$workspace"

mkdir -p public

# A page and a stylesheet with a look of their own: named colours, a font, a
# card. The look question tells the variants to copy these, so they have to be
# there to be read. Nothing here mentions a history view -- that is the page the
# prompt asks for, and how it looks is the open decision.
cat > public/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Greeter</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="bar">
    <h1>Greeter</h1>
  </header>
  <main>
    <section class="card">
      <h2>Say hello</h2>
      <form>
        <input name="name" placeholder="Name" aria-label="Name">
        <button type="submit">Greet</button>
      </form>
    </section>
  </main>
</body>
</html>
HTML

cat > public/styles.css <<'CSS'
:root {
  --ink: #1f2933;
  --paper: #fdf8f0;
  --accent: #e8590c;
  --line: #e4d9c8;
}

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Georgia", serif;
}

.bar {
  background: var(--accent);
  color: var(--paper);
  padding: 0.75rem 1.5rem;
}

.bar h1 {
  margin: 0;
  font-size: 1.25rem;
  letter-spacing: 0.04em;
}

main {
  max-width: 40rem;
  margin: 2rem auto;
  padding: 0 1rem;
}

.card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 1.25rem;
}

button {
  background: var(--accent);
  color: var(--paper);
  border: 0;
  border-radius: 4px;
  padding: 0.4rem 0.9rem;
  font-family: inherit;
}
CSS

git add -A
git commit -qm "feat: a web page for the greeter"
git push -q origin main

# Same self-check the shared fixture makes: a fixture that comes out wrong
# reads as the plugin failing.
[ -f public/index.html ] || { echo "scaffold.sh: public/index.html is missing" >&2; exit 1; }
[ -f public/styles.css ] || { echo "scaffold.sh: public/styles.css is missing" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "scaffold.sh: tree is dirty" >&2; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || { echo "scaffold.sh: not on main" >&2; exit 1; }
