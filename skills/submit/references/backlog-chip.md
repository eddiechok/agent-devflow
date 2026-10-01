# A request that came from a flow chip

`submit` step 7 reads this when the request carries an `Also parked as` line.

**A request with an `Also parked as .devflow/backlog/<name>.md` line** came from a `flow`
chip. End the commit body with `Backlog: .devflow/backlog/<name>.md`, and put the same line
under **What** in the PR body — whether or not the file was in this checkout. With nothing
to commit, the PR body alone carries it. It is what a later `flow` run looks for before
building that file, so a feature ships once.
