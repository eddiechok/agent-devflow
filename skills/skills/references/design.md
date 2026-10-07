# Design skills

A repo with a UI gets **one design skill**, plus `web-design-guidelines`. The design skills
that generate (all but the last) each give the model a style direction, and two directions
installed together compete: the model follows whichever it read last, so the same repo looks
different from one session to the next. `minimalist-skill` conflicts with `frontend-design`
head on: flat, quiet and no gradients against a bold direction.

`web-design-guidelines` only reviews UI code against a checklist. It sets no style, so it
clashes with nothing and is suggested alongside whichever skill is picked.

## The table

Sizes and stars were read on 2026-10-07 from the installed copy or the repo.

| Skill | Size | Stars | Carries | Install |
|---|---|---|---|---|
| `frontend-design` | 41 lines | 37,477 (`anthropics/claude-plugins-official`, Apache-2.0) | skill only; bold aesthetic | `claude plugin install frontend-design@claude-plugins-official --scope project` |
| `taste-skill` | 1,206-line `SKILL.md` | 93,170 (`Leonxlnx/taste-skill`, MIT) | skill only; landing pages, portfolios, redesigns | `npx skills add Leonxlnx/taste-skill` |
| `impeccable` | about 5,500 lines of markdown in 55 files | 77,769 (`pbakaus/impeccable`, Apache-2.0) | skill plus design, audit and polish commands | `npx impeccable install` |
| `ui-ux-pro-max` | 587 lines of markdown | 133,626 (`nextlevelbuilder/ui-ux-pro-max-skill`, MIT) | skill plus searchable design data; web, mobile and desktop | `claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill --scope project`, then `claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill --scope project` |
| `minimalist-skill` | 85 lines | unconfirmed | skill only; flat editorial, no gradients | unconfirmed |
| `redesign-skill` | 178 lines | unconfirmed | skill only; audits and upgrades existing UI | unconfirmed |
| `web-design-guidelines` | 39 lines | 32,008 (`vercel-labs/agent-skills`, no license) | skill only; review-only | `npx skills add vercel-labs/agent-skills` |

`minimalist-skill` and `redesign-skill` are probably part of `Leonxlnx/taste-skill`, and that
is **unconfirmed**. Before printing an install line for either, confirm the source: read the
repo's file list with `gh api repos/Leonxlnx/taste-skill/contents`, and print a line only if
the skill's folder is there. If it is not, say the source could not be confirmed and print no
command.

`web-design-guidelines` has no license, so nothing is copied from it. It is named and linked.

## Facts first

Read these before asking anything, so each question can recommend an answer:

- `react-native`, `expo`, `electron` or `tauri` in the manifest or its dependencies
- a `tailwind.config.*` file
- a `components/ui` folder
- how much UI code there is: a handful of components, or a lot of screens

No UI at all (no framework, no components, no pages) means skip this whole file.

## The three questions

Ask them as one round, with a recommended answer for each, taken from the facts. Skip
question 3 when the repo has no UI yet.

**1. What is the UI for?**

| Answer | Suggest |
|---|---|
| landing, marketing site or portfolio | `taste-skill` or `frontend-design` |
| app screens | `impeccable` |
| mobile or desktop app | `ui-ux-pro-max` |

Recommend mobile or desktop when the facts show `react-native`, `expo`, `electron` or
`tauri`. Recommend app screens when `components/ui` holds a lot of screens.

**2. What look?**

| Answer | Suggest |
|---|---|
| bold | `frontend-design` for a small UI, `taste-skill` for a big one |
| clean and quiet | `minimalist-skill` |
| no view | `ui-ux-pro-max` |

Recommend "no view" when the repo shows nothing that decides it.

**3. New or improve?** (only when UI exists)

| Answer | Suggest |
|---|---|
| new | the pick from questions 1 and 2 stands |
| improve | `impeccable` or `redesign-skill` |

Recommend "improve" when there is a lot of UI code already.

When the answers point at two different skills, pick the one question 1 named, and say in
one line which answer it came from. Never print two design skills.

## Already installed

Read the installed list first (step 1 of `SKILL.md`). The design skills are loose skills in
`~/.claude/skills/<name>/` (user scope) or `.claude/skills/<name>/` (project scope), or
plugins.

- **Several design skills installed** (two or more of `frontend-design`, `taste-skill`,
  `impeccable`, `ui-ux-pro-max`, `minimalist-skill`): print a clash warning naming them, and
  say their directions are competing. Name the one that fits, and leave the rest to the human.
- **The pick is installed at user scope only**: it is not in the repo, so a collaborator or a
  cloud session does not have it. Print the commands to move it to project scope. They are
  printed and never run: the human runs them, and checks first that the project copy is the
  same version.

For a loose skill:

```
cp -R ~/.claude/skills/<name> .claude/skills/<name>
rm -R ~/.claude/skills/<name>
```

For a plugin:

```
claude plugin uninstall <plugin>@<marketplace> --scope user
claude plugin install <plugin>@<marketplace> --scope project
```

Print the second line of the plugin pair only after the first, and print neither for a skill
already installed at project scope.
