# Sources

The bookmark list. Read each page in the session (`WebFetch`, or `curl` and `grep`), never
through a researcher agent. Quote every number with its URL. A summarizing fetch can garble
a number, so where two places on a page disagree, say so in the table instead of picking one.

To add a page, add a line here. Every URL is an https link.

## Where the settings live

- https://code.claude.com/docs/en/settings: the main session's default model and effort are
  the `model` and `effortLevel` keys in `~/.claude/settings.json`. `/model` and `/effort`
  save defaults there. `--model`, `--effort` and `ANTHROPIC_MODEL` override one session.

## Which model

- https://platform.claude.com/docs/en/about-claude/models/choosing-a-model: Anthropic's
  matrix. Fable 5.2 is highest capability and multistep deep research. Opus 5.5 is complex
  agentic coding. Sonnet 5.5 is code generation and agentic tool use. Haiku 5.5 is lowest
  latency and price, and subagent tasks. It has no code-review row.
- https://cognition.com/frontiercode: FrontierCode 2.0 (132 tasks, 27 Oct 2026), each model
  at its best effort: Fable 5.2 49.1%, Opus 5.5 45.5%, Sonnet 5.5 41.0%, Haiku 5.5 27.7%.
  The ranked list is in the page's JSON-LD `ListItem` data, so `curl` and `grep` it. Effort
  per row and cost are not readable there.
- https://cognition.com/blog/frontier-code-2.0: models can score lower at higher effort,
  mainly from scope blockers. Opus 5 scope is 69.2% at low and 51.1% at max on 1.1.

## Which effort

- https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence:
  Opus 5.5 on the SWE-bench Pro subset, per task: low 87.4% at $0.11, medium 92.8% at $0.21,
  high 95.3% at $0.29, xhigh 96.7% at $0.74 (Anthropic-internal, directional). "For most
  agent workloads, start with Claude Opus 5.5 at its default effort (medium)". It has no
  code-review guidance. The page is about 217k characters, so `WebFetch` needs offsets 0,
  100000 and 200000.
- https://platform.claude.com/docs/en/build-with-claude/effort: Sonnet 5.5, "start with
  medium for well-specified tasks and move to high for harder or longer ones". Haiku 5.5
  medium. Fable 5.2 high.

## Optional

- https://www.qodo.ai/blog/which-llm-should-review-your-code/: review. Qodo (Oct 12, 2026),
  Opus 5.5 at high, F1 56.8, $1.00 per PR. Vendor-run. Its Sonnet 5.5 numbers disagree
  between the text and the table, so flag that if you quote it.
- https://openrouter.ai/benchmarks/tau2-bench-airline: tool use. τ²-bench Airline, Sonnet 5.5
  78.8% (rank 5, $0.16 per task), Opus 5.5 75.3% (rank 32, $0.34 per task). No effort split.

## Not fit now

Checked and left out. Look again only if the reason below stops being true.

- https://swe-rebench.com: no 5.5 models.
- https://www.tbench.ai/leaderboard: Terminal-Bench has no effort column.
- https://artificialanalysis.ai/models: only Fable 5.2 and Opus 5.5 at max.
- https://metr.org/time-horizons: no longer updated.
