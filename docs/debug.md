# debug, in detail

Why `debug`'s phases are what they are. The steps themselves are in
[the skill](../skills/debug/SKILL.md), and where each idea came from is in
[provenance](provenance.md).

## Why debug never fixes anything

`build` already owns test-first: write the test, watch it fail, make it pass. A bug is not
a special case of that loop, it is the same loop with an extra step in front — you have to
know where the test goes before you can write one. `debug`'s only job is finding that seam.

Splitting the two skills at that line, rather than letting `debug` fix what it finds, avoids
a real failure mode: a fix written by the same pass that found the cause tends to get tested
by the command that already proved the cause, which is the loop confirming itself rather
than a fresh test proving the fix. Handing the cause and the red command to `build` keeps
the test-first discipline in the one place that already enforces it, instead of building a
second, weaker copy of the same five gates inside `debug`.

## Why flow only routes here for an unknown cause

A bug you can already point at — the file, the function, the line — has nothing left for
Phase 1 to discover. Routing it through `debug` anyway would spend a whole loop confirming
what was already known, for no benefit; it goes to `build` directly, same as any other
change. `debug` earns its keep exactly where `build`'s test-first loop cannot start on its
own: when nobody yet knows where the test goes.

## Why the loop comes before everything else

Every phase after Phase 1 — reproducing, ranking causes, probing them — is reading the
output of a command. Without a command that reliably goes red on the reported bug, "probing
a hypothesis" is a guess dressed up as a step, and "confirming a cause" is agreeing with
yourself. The loop is where the actual signal comes from; the rest of the skill exists to
use it well.

That is also why a loop that cannot be built stops the skill rather than lowering the bar.
Proceeding to Phase 3 without one would produce a ranked list of hypotheses that look
rigorous and were never checked against anything, which is worse than admitting there is
nothing to check them against yet.

## Why the ranked list is shown, not waited on

A human often has domain knowledge that re-ranks the list instantly — "we deployed a change
to #3 yesterday" — so showing it is worth the two seconds it takes to read. But `debug` runs
inside `flow`'s pipeline toward `build` and `submit`, and a step that blocks on a reply the
human may not have yet stops a pipeline that was working. So the list is a courtesy, not a
gate: seeing it costs nothing, and waiting on it would cost the one thing an automated
pipeline has going for it.

## Why every probe is tagged with the existing `[DBG-` marker

`build` already tags temporary logging with `[DBG-`, and `submit` step 3 already greps for
it before anything ships. Inventing a second tag for `debug`'s own probes would need a
second sweep, in a second place, checked by a second rule — and the day one of the two greps
drifts from the other, a marker slips through silently. One tag, one sweep, shared by both
skills, means a marker `debug` forgot to clean up is still caught by the same net that
already exists.
