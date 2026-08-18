# A review that does not get cheaper by accident

Branch: `claude/model-routing-devflow-um0ref`
Issue: none

**Written during the work, from the request that drove it.** The question asked was whether model routing was applied in devflow. It was not — nothing in the repo named a model or an effort level — so the branch became the work of applying it.

## Why

An agent with no `model:` and no `effort:` inherits the session. Both fields are optional and both default to inheriting, so leaving them out is spelled exactly like choosing them.

That is fine for a skill, which runs in front of you. It is not fine for the two review agents. They are the last thing between a branch and a pull request, they run in fresh contexts you never see, and a review that ran on a weaker model than intended still prints a review and still says nothing went wrong. The failure is silent in the same way a truncated `description` is silent: the file looks right and the run looks finished.

## What was checked first

`model:` and `effort:` are real skill frontmatter fields, not only agent ones. That was verified against the docs before anything was designed, because `claude plugin validate` turned out to prove nothing here — it accepts an invented key (`zzzTotallyBogusKey`) exactly as quietly as it accepts `model`, so a passing validate was not evidence either way.

Two findings from that check shaped the scope:

- **A skill's `model:` applies for the rest of the turn**, not for the skill. devflow chains `flow` → `build` → `submit` inside one turn, and there is no pop-back, so one skill setting a model leaves it set for every skill after it. Routing the skills is all-or-nothing: six files, or a leak.
- **Size cannot drive it.** `flow` picks Quick, Standard or Deep at runtime; `model:` is fixed on disk; and a skill cannot type `/model` at itself — the same wall `/code-review` hit, for the same reason. There is no version of this that routes by size without three copies of `flow`.

## What was checked after

The frontmatter test proves the fields are on disk and spelled right. It does not prove they do anything — it reads back what was just written, which is the shape of test this repo already has a commit against.

So the pin was checked against a running agent, by differential:

```
claude --plugin-dir . --model haiku -p "spawn devflow:reviewer, ask which model it is"
```

| `agents/reviewer.md` | The subagent answered |
|---|---|
| `model: opus` present | Claude Opus 5 |
| the two lines deleted | Claude Haiku 4.5 |

Same session model, same prompt, one difference. The pin is what moved it.

**This is deliberately not an eval case.** A case cannot pin its own session model — `--model` is a runner flag that overrides every case at once — so on the usual Opus run, an eval asserting "the reviewer is on Opus" passes whether or not the frontmatter says anything. That is a case that passes by finding nothing, which is the failure `test-frontmatter.py` opens by describing. The contract test guards the field against silent deletion, which is devflow's job; whether `model:` routes at all is Claude Code's guarantee, and testing it here would mostly test the harness.

## Assumptions

- Agents only. Subagents are separate contexts, so pinning them cannot leak into the skill chain, and it is the whole of the risk with none of the six-file coupling.
- Both agents pin the **same** model and effort. The two reports are never ranked against each other; a weaker model on one axis ranks them anyway, without saying so.
- `opus` and `xhigh` because a missed finding reaches `main`. Review runs once per branch, not once per turn, so the cost is bounded by how often you open a PR.
- `inherit` is rejected by the test rather than allowed. It is a real value, but it is spelled the same as forgetting.

## Pieces

1. [independent: no] The frontmatter test requires every agent to pin `model` and `effort`, with values from the documented sets.
   Verify: `python3 skills/test-frontmatter.py`

2. [independent: no] `reviewer` and `spec-reviewer` pin `model: opus` and `effort: xhigh`.
   Verify: `python3 skills/test-frontmatter.py`

3. [independent: yes] The PyYAML cross-check compares booleans by YAML spelling. Found while running the suite, not asked for: it was already failing on `main`, so the branch could not otherwise show a green run.
   Verify: `python3 skills/test-frontmatter.py`

## Not done

Routing the six skills, and routing by size. Both are written up in the README's "What is not here yet" with the reason, so the next person does not rediscover the turn-scope rule the hard way.
