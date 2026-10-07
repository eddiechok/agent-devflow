# The look question

Read this when a decision question in the rounds is about how something looks, the human
picked "Show me the variants", and the size is Standard or Deep. Quick never gets here.

## What it is

One plain HTML file with 2 or 3 variants of the thing, shown to the human so they pick by
seeing. The file is made only after "Show me the variants" is picked, never before. The
variants carry the same names as the text options: "A: sidebar", "B: tabs".

The file is thrown away. Only the pick and why go on: the pick and why are recorded as the
answer to the question, the same as any other answer, and build starts from that.

## Where it goes

Make the folder with `mktemp -d`, so it sits outside the repo, and write the file in it.
Never a file in the repo, and never a tracked file edited: there is no prototype branch,
no `?variant=` code in the app, and no dev server. A variant on the real page edits
tracked files before go, and the human has not said go yet; a prototype branch moves the
whole folder, which step 0c of the flow skill keeps off a folder another session is using.

Open it in the desktop browser pane where there is one. Otherwise it prints the path and
stops there, one line:

```
→ **variants** /tmp/tmp.k3Jx9/variants.html — open it, then pick
```

## How the variants look

- Use the repo's design skill if one is installed. If none is, still follow the
  look the app already has.
- Use the app's own look: its colours, its fonts and its parts, read from its own CSS or
  theme. A variant in a style the app does not have answers a question nobody asked.
- Make the variants really different in structure: a sidebar against tabs, not the
  same layout with another shade. Three small tweaks of one card grid is not a choice.
- Keep it one file with inline CSS, small enough to read at a glance. No build, no
  install, no network.

## The UX check

Before showing the variants, check them with the UX skill that is installed. The table of
UX skills is [the skills skill's ux.md](../../skills/references/ux.md): find an installed
one by matching its plugin names against `claude plugin list --json`, then run that skill
on the file. An entry counts only with `"enabled": true` and either user scope or a
`projectPath` that is this repo's top folder: the list also shows installs from other
folders, disabled here. When impeccable is installed, it is the check: run
`/impeccable critique` on the file, and no table plugin is needed. It counts as an
`impeccable@impeccable` entry by the same rule, or as a loose skill in
`.claude/skills/impeccable/` or `~/.claude/skills/impeccable/`, which is where
`npx impeccable install` puts it.
Fix what the check names that would change which variant wins, and show the file after that.

If none of these is installed, skip the check, print this one line, and
carry on to the variants, and never run /devflow:skills from here: it only suggests, and
the human runs it when they choose to:

```
– **ux** no UX skill installed — run /devflow:skills to get one
```

## Then ask again

After the variants are shown, ask the same question again with the same options, the way
the flow skill asks again after "explain this". "Show me the variants" is not offered a
second time. The answer is the pick, with the reason when the human gave one.

## Where there is no popup tool

Evals and `claude -p` have no popup tool. The numbered list offers "Show me the variants"
as one more item, and the path of the HTML file is printed, as above. When the list is
answered with that item, make the file and ask the question again.
