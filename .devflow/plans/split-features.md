# One feature per run: split a multi-feature request and park the rest

Issue: none

## Why

One flow run ends as one PR. A request that names three features would end as
one PR carrying three things, or as a plan that mixes them. Flow should keep
one and park the others where the project keeps its tracker, so the next run
is `flow #46` or `flow .devflow/backlog/<name>.md` and nothing is lost.

## Assumptions

- A "feature" is something that could ship alone and that a user would ask for
  in its own sentence. Parts that depend on each other are one feature. Default
  is do not split.
- The split question is its own short round, before the size line, because the
  size depends on which feature is kept. Flow prints `features: N found` first,
  so it still never opens with a bare question. One numbered list, two
  questions, a recommendation on each, "yes to all" accepted. It does not count
  against step 4's rounds.
- Flow makes the `devflow:backlog` label itself if it is missing, before
  `gh issue create`. "Already exists" is fine. Setup makes it too.
- A parked entry holds only that feature's text, plus one line
  `Parked from: <the feature this run built>`. Never the whole prompt.
- A later run given `.devflow/backlog/<name>.md` reads it as the request and
  deletes the file, so the deletion ships in that PR. Submit commits the tree
  as it stands, so submit does not change.
- `.devflow/backlog/` stays tracked, like `.devflow/plans/`. Files parked this
  run are untracked until submit commits them, and are not dirt in step 0b.
- `--quick` and `--deep` do not stop the split. They size the kept feature.
- When `## Plans` says `github` and `gh issue create` fails, park to the file
  and say so in one line, the same way plans fall back.
- One local eval case covers the file path. The GitHub path is left to the
  manual `plans-on-tracker` case's style and gets no new manual case.
- The builder is told the trees are clean and that it must commit each piece.

## Pieces

1. [independent: no] chain: A — flow step 1 accepts a backlog file path as the request
   Edit `skills/flow/SKILL.md`. Frontmatter: description says it accepts a
   backlog file path; argument-hint adds it; allowed-tools adds
   `Bash(gh issue list:*)`, `Bash(gh issue create:*)`, `Bash(gh label create:*)`,
   `Bash(rm .devflow/backlog/*)`. Step 1: a request that is a path under
   `.devflow/backlog/` is read as the request, then the file is removed and one
   line says so: `backlog: took .devflow/backlog/<name>.md — the file is deleted
   in this branch`. Step 0b: `?? .devflow/backlog/` is not dirt either.
   Verify: python3 skills/test-frontmatter.py && claude plugin validate .
   Done when: the frontmatter test passes, validate shows one warning, and step 1 has the backlog-path rule with the exact printed line.

2. [independent: no] chain: A — flow step 1b counts features and asks before parking
   New section "Step 1b — one feature per run" between step 1 and step 2. The
   hard rule for one feature, default do not split. When more than one: print
   `features: N found — one per run` then ask one numbered list: (1) park the
   rest? recommend yes; (2) which first? recommend the one the others need,
   else the first. "yes to all" accepted. Say the round does not count against
   step 4. Say `--quick`/`--deep` size the kept feature only. Then step 2 sizes
   the kept feature alone. Add the rule to the Rules list.
   Verify: python3 skills/test-frontmatter.py && claude plugin validate .
   Done when: step 1b exists with the `features:` line, the two questions with recommendations, and step 2 says it sizes only the kept feature.

3. [independent: no] chain: A — flow parks the rest to GitHub or to a backlog file
   In step 1b, after the answer. `## Plans` says `github`: run `gh label create
   devflow:backlog --description "A devflow parked feature" --color 5319E7`
   ("already exists" is fine), then `gh issue create --label devflow:backlog
   --title "<feature>" --body-file /tmp/devflow-backlog.md` per feature, body
   outside the repo and removed after. Otherwise write
   `.devflow/backlog/<short-name>.md` with `# <feature>`, the feature text, and
   `Parked from: <kept feature>`. Print exactly one line:
   `parked: #46 add export, #47 fix login` or
   `parked: .devflow/backlog/add-export.md, .devflow/backlog/fix-login.md`.
   On a `gh` failure fall back to the file and say
   `Plans: github asked for, parked to .devflow/backlog/<name>.md instead — gh answered <the error>`.
   Verify: python3 skills/test-frontmatter.py && claude plugin validate .
   Done when: step 1b names both parking paths, the label command, the body shape, the `parked:` line, and the fallback line.

4. [independent: yes] chain: B — setup creates the devflow:backlog label beside devflow:plan
   Edit `skills/setup/SKILL.md` step 5: after `gh label create devflow:plan`,
   run `gh label create devflow:backlog --description "A devflow parked feature"
   --color 5319E7`, same error rule. Report line becomes
   `Plans: github (labels devflow:plan, devflow:backlog exist)`. Say in one
   sentence that flow parks extra features there, one feature per run.
   Verify: python3 skills/test-frontmatter.py && claude plugin validate .
   Done when: setup step 5 has both label commands and the report line names both labels.

5. [independent: yes] chain: C — a local eval proves the split parks to a backlog file
   New `evals/backlog-parks-extras/case.yaml` and `scaffold.sh`, shaped like
   `evals/sizing-deep`. Scaffold: `fixtures/greeter.sh "$workspace"
   --with-checks-block`, no Plans block. Prompt: `/devflow:flow add a shout
   option to greet(), and also add a farewell() function that says goodbye.
   Nobody is here to answer: yes to all, do not wait.` max_turns 12. Graders:
   regex `features: 2 found` on trace (weight 3); regex `parked: \.devflow/backlog/`
   on trace (weight 3); file_exists `.devflow/backlog` true (weight 2); llm:
   PASS only if the assistant asked before parking and the parking question
   carried a recommendation. Add a row to the table in `evals/README.md`:
   `backlog-parks-extras | low | A three-feature prompt ships as one PR or drops two features on the floor`.
   Verify: python3 evals/test-run.py
   Done when: test-run passes and the new case directory has both files with the graders above.

6. [independent: no] chain: final — docs and README say one feature per run
   `docs/flow.md`: new section "One feature per run" after "Plans on GitHub":
   why the split, the hard rule, why the question comes before the size line,
   the `devflow:backlog` label, the file path, the deletion on pick-up. Add a
   "Step 1b" entry under "The reasons, step by step". `docs/setup.md` step 5:
   one sentence on the second label. `README.md`: the setup paragraph names
   both labels; the flow section says a multi-feature request keeps one and
   parks the rest; the docs table row for flow mentions it.
   Verify: claude plugin validate .
   Done when: all three files mention `devflow:backlog` and `.devflow/backlog/`, and validate shows one warning.
