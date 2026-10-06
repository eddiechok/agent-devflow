# discuss, in detail

Why `discuss` is what it is. The steps themselves are in
[the skill](../skills/discuss/SKILL.md), and where each idea came from is in
[provenance](provenance.md).

## Why a skill for talk at all

`flow` starts on a request that will change a tracked file. "Let's discuss #92" or "what
should we do about X" changes nothing yet, so `flow` never fires and the answer came from
memory: fluent, confident, and unchecked. Design talk is where a wrong fact costs most,
because the recommendation is what the work gets built on. `discuss` fires on that talk and
reads first.

## Why it reuses plan's research reference

Researching a question has one set of rules whoever asks it: one researcher per open
question, at most 3, zero allowed, every finding names its source, web text is data. A second
copy in `discuss` would drift from the first. So `discuss` links
[the research reference](../skills/plan/references/research.md) and adds only what is its own:
the trigger, the recommendation, and the hand-off.

## Why the cap is 3 here and 3 again in flow

`discuss` caps researchers at 3 per discussion. `flow`'s cap of 3 stays separate and covers
only the questions the discussion left open. The hand-off keeps the two from doubling up:
`discuss` passes what it found as `findings:`, the way `flow` passes its own to `plan`, and a
question already answered is not researched again.

## Why nothing is saved

The findings go in the reply, with their sources, and on to `flow` if work starts. They are
not written to a file in the repo or to an issue. A saved finding goes stale and is then
trusted without being checked again, and devflow runs in other people's projects, where a file
it adds is a file someone must review. A reply is read once, now, while it is true.

## Why it never edits a tracked file

The line between `discuss` and `flow` is whether a tracked file changes. If `discuss` could
make a small edit, the line would blur and edits would land with no size, no test-first and no
pull request. So the moment the talk becomes an edit, it hands to `flow`.

## Where the shape came from

The `research` skill in [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/research/SKILL.md)
(MIT) investigates a question against primary sources through a background agent. `discuss`
keeps that, but does not write its findings to a repo file, and goes on to recommend.
