# The vendor table

One row per vendor. A row fires on its file signal, and only on that: a repo that does not
carry the signal is never suggested the row, whatever its README says.

**The source bar.** Official vendor repo, or 1k+ stars. A row in this table clears it
already; a skill found by `npx skills find` has to clear it before it is listed. Under 100
stars, say nothing.

Stars and licenses below were read on 2026-10-07 from each repo. The install lines are the
vendor's own, moved to project scope.

## Railway

- **Signal:** `railway.json` or `railway.toml`
- **Source:** `railwayapp/railway-skills`, official vendor repo, 326 stars, MIT
- **Plugin:** `railway`, from the marketplace `railway-skills`
- **Carries:** skills, hooks and an MCP server (`railway`, http, `https://mcp.railway.com`)
- **Size:** one plugin; the plugin folder is `plugins/railway`. Read the skill count at run
  time (step 5 of `SKILL.md`)
- **Install:**
  - `claude plugin marketplace add railwayapp/railway-skills --scope project`
  - `claude plugin install railway@railway-skills --scope project`
- **MCP-only alternative:** `claude mcp add railway --transport http https://mcp.railway.com`.
  The plugin already carries this server, so never print both.

## Medusa

- **Signal:** `@medusajs/` in `package.json`
- **Source:** `medusajs/medusa-agent-skills`, official vendor repo, 225 stars, license field
  empty
- **Plugins:** `medusa-dev`, `learn-medusa`, `ecommerce-storefront`, `medusa-cloud`, all from
  the marketplace `medusa`. Suggest `medusa-dev` for a repo that builds on Medusa; name the
  other three in one line and let the human pick
- **Carries:** read at run time
- **Install:**
  - `claude plugin marketplace add medusajs/medusa-agent-skills --scope project`
  - `claude plugin install medusa-dev@medusa --scope project`

## Cloudflare

- **Signal:** `wrangler.jsonc` or `wrangler.toml`
- **Source:** `cloudflare/skills`, official vendor repo, 2997 stars, Apache-2.0
- **Plugin:** `cloudflare`, from the marketplace `cloudflare`
- **Carries:** read at run time
- **Install:**
  - `claude plugin marketplace add cloudflare/skills --scope project`
  - `claude plugin install cloudflare@cloudflare --scope project`

## Supabase

- **Signal:** a `supabase/` folder, or `@supabase/` in `package.json`
- **Source:** `supabase/agent-skills`, official vendor repo, 2704 stars, MIT
- **Plugin:** `supabase`, from the marketplace `supabase-agent-skills`
- **Carries:** read at run time
- **Install**, either one:
  - `npx skills add supabase/agent-skills`
  - `claude plugin marketplace add supabase/agent-skills --scope project`, then
    `claude plugin install supabase@supabase-agent-skills --scope project`

## Stripe

- **Signal:** `stripe` in the dependencies of a manifest (`package.json`, `pyproject.toml`,
  `Gemfile`, `composer.json`, `go.mod`)
- **Source:** `stripe/ai`, official vendor repo, 1859 stars, MIT
- **Plugin:** `stripe`, from the marketplace `claude-plugins-official`
- **Carries:** read at run time
- **Install:** `claude plugin install stripe@claude-plugins-official --scope project`. The
  marketplace is Anthropic's own and is already known to Claude Code, so there is no
  `marketplace add` line

## Signals with no vendor row

These are not in the table, so they go to the `npx skills find` fallback, with the query
named here:

| Signal | Query |
|---|---|
| `Dockerfile` | `docker` |
| `playwright.config.*` | `playwright` |
| an `openapi.*` or `swagger.*` file | `openapi` |

A result still has to clear the source bar above before it is listed.
