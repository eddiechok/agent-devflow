# The curl fallback, when `gh` is not installed

`command -v gh` finds nothing means the same REST calls this project makes through `gh
api` go through `curl` instead. Every issue call in `flow` and `plan` uses this form when
`gh` is missing:

```
curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN" "https://api.github.com/repos/<owner>/<repo>/issues?labels=devflow:plan&state=open"
```

Read `<owner>/<repo>` from `git remote get-url origin`. If the remote does not name a
GitHub repo, write them in yourself. Never print `$GH_TOKEN`, and send it to
`api.github.com` and no other host. In a cloud session it holds a placeholder the proxy
swaps for the real credential. `curl` has no `--jq`, so read the JSON it returns yourself
and skip every entry with a `pull_request` key. Read one body from
`https://api.github.com/repos/<owner>/<repo>/issues/<n>`. To open an issue, build its
JSON with `json.dumps` and post that. Write it to a fresh file — never a fixed path,
which another session or another user can reach first:

```
mktemp "${TMPDIR:-/tmp}/devflow-issue.XXXXXX"
```

The path it prints is `<json file>` below:

```
python3 -c 'import json,sys; print(json.dumps({"title": sys.argv[1], "body": open(sys.argv[2]).read(), "labels": [sys.argv[3]]}))' "<title>" <body file> <label> > <json file>
```

```
curl -sS --fail-with-body -H "Authorization: token $GH_TOKEN" --data-binary @<json file> https://api.github.com/repos/<owner>/<repo>/issues
```

Remove `<json file>` after. A missing label is a POST of
`{"name": ..., "color": ...}` to `https://api.github.com/repos/<owner>/<repo>/labels`.
Only when `curl` fails too does the work fall back to a file.
