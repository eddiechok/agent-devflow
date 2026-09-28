# If there was no `## Deploy` block, offer to write one now

**Only when the live check just passed.**

Show what you actually ran, and ask:

```
No ## Deploy block in CLAUDE.md. I just ran:
   Deploy: npx wrangler deploy
   Verify: https://edxtech.com.my  (200, serving the new build)
   Wait:   48s observed, suggest 120s
Write this into CLAUDE.md?
```

Ask rather than assume.

What may go in it:

- **Only lines you exercised this run.** If the deploy happened on merge and you ran no command, write `Verify` and `Wait` and leave `Deploy` out entirely. An absent line is correct there, not a gap to fill in.
- **One line per command you actually ran.** If it took two, write two.
- **`Wait` from what you observed, rounded up.** Not a guess, and not the exact figure either — that will be too tight on the first slow day.
- **Never a command you did not run.** Same rule `setup` follows, and the reason this offer lives here instead of there.
