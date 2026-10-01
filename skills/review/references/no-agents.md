# When the harness will not let you spawn an agent

`review` reads this only when an axis cannot start.

Some sessions forbid starting an agent unless the human asked for one, in the system prompt. Look at your own instructions: if something there says not to spawn an agent unless asked, this section applies, and otherwise it does not. Where it applies, neither axis can start on its own.

Do not skip it quietly, and do not review the code yourself instead — this session wrote it, which is the thing the review agents exist to avoid. Say it in one line and ask:

```
This harness only starts agents when you ask. Say "run the review" and every axis goes.
```

If that answer does not come, the axis **did not run**. Print `– **review** agents not permitted — axis NOT RUN`, report it as `NOT RUN` in step 4 with the reason, and let `submit` carry it into the PR.
