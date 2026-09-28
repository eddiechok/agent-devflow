# A PR that is merged or closed is not an open one

Step 0's three cases — follow-up, hand to `tend`, or new work — are all about an **open**
pull request. If the branch's PR came back `MERGED` or `CLOSED`, this branch is finished,
and piling new work on it is worse than piling it on an open one — the diff against the
default branch will be empty or wrong, because its commits are already in.

Treat it as new work, and say so: fresh branch, cut from the default branch ref, not from
here. The same applies when the branch is simply behind — start from the ref, not from
where you happen to be standing.
