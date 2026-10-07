# UX skills

A repo with a UI gets **one UX skill**, beside its one design skill. A design skill sets a
look; a UX skill checks whether the screen works: hierarchy, flow, copy, accessibility. The
two do not compete, because the UX skills below set no style. Two UX skills would give
overlapping critiques, so one is the most a list holds.

The look question in the flow skill reads this file too: it finds an installed UX skill by
matching the plugin names below against `claude plugin list --json`. An entry counts only
with `"enabled": true` and either user scope or a `projectPath` that is this repo's top
folder; the list also shows installs from other folders, disabled here.

## The table

Stars and sizes were read on 2026-10-07 from the repo. They are a reference, not what gets
printed: step 3a reads them fresh each run for every skill it lists, and runs a live search
on top of this table. A find that passes the source bar may be recommended over a row here,
with the reason.

| Plugin | Skills used | Size | Stars | Install |
|---|---|---|---|---|
| `design@knowledge-work-plugins` | `design:design-critique`, `design:ux-copy`, `design:accessibility-review` | 7 skills in the plugin; design-critique 118 lines, ux-copy 107, accessibility-review 128 (WCAG 2.1 AA) | 26,788 (`anthropics/knowledge-work-plugins`, Apache-2.0) | `claude plugin marketplace add anthropics/knowledge-work-plugins --scope project`, then `claude plugin install design@knowledge-work-plugins --scope project` |
| `ux-design@wondelai-skills` | `ux-design:ux-heuristics`, `ux-design:ios-hig-design` | 11 skills in the plugin; line counts not read | 2,351 (`wondelai/skills`, MIT; a collection of 65 skills, so its install count counts, not its stars) | `claude plugin marketplace add wondelai/skills --scope project`, then `claude plugin install ux-design@wondelai-skills --scope project` |

`design@knowledge-work-plugins` is not skills only: `design/.mcp.json` turns on 9 MCP
servers (Slack, Figma, Linear, Asana, Atlassian, Notion, Intercom, Google Calendar, Gmail),
each asking for a login. Say so on its entry, under what it carries.
`ux-design@wondelai-skills` carries skills only.

Both set no style. `ux-heuristics` covers Krug, Nielsen's 10 heuristics, dark patterns and
accessibility; `design-critique` covers usability, hierarchy, consistency and accessibility.

The session names (`design:design-critique`, `ux-design:ux-heuristics`) are **inferred**
from the plugin's name and the skill's folder, not read from a doc. Match on the plugin
name, which `claude plugin list --json` prints, and not on the session name.

## Pick one

No new question. Take the answer to "What is the UI for?" and the repo facts that
`design.md` already reads, and go down the table; first match wins, and say in one line
which row it was.

| # | When | UX skill |
|---|---|---|
| 1 | the design pick is `impeccable` | none |
| 2 | the UI is a mobile app (`react-native` or `expo`) | `ux-design@wondelai-skills` |
| 3 | anything left: app screens, a landing or marketing site, a portfolio, a desktop app | `design@knowledge-work-plugins` |

Row 1 first, because `impeccable` carries its own UX review: `/impeccable critique` scores
Nielsen's 10 heuristics. A design skill that already carries one means no second UX skill,
and that command is the check. Say so in one line rather than leaving a gap in the list.

A desktop app (`electron`, `tauri`) is web screens in a window, so it takes row 3.

## Already installed

Read the installed list first (step 1 of `SKILL.md`). When the pick's plugin is already
installed, drop it with the line saying so. When both are installed, do not warn: they set
no style, so they do not clash.
