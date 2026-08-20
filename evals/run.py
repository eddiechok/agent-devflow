#!/usr/bin/env python3
"""Run devflow's eval cases without `claude plugin eval`.

`claude plugin eval` is gated — it exits 1 with "currently in early access"
before running anything — so the cases in this directory were unrunnable. This
runs the graders that need no model, which is most of them: of the 33 graders
across the seven cases, 26 are `regex`, `tool_used`, `tool_order` or
`file_exists`, and every one of those is decidable from a `stream-json` trace.

**It does not run the `llm` graders, and it never reports one as passed.** They
come back `skip`, they stay out of the score's denominator, and the summary
prints the count. A skipped grader is not a passing grader, the same way
`NOT RUN` is not `none`.

Usage:

    python3 evals/run.py                      # every case
    python3 evals/run.py --case sizing-*      # a glob
    python3 evals/run.py --case full-loop --runs 1
    python3 evals/run.py --case full-loop --dry-run   # parse and print, run nothing

When `claude plugin eval` is available to you, prefer it — it also scores the
`llm` graders and the no-plugin baseline arm. This is the subset that works
today.
"""

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)


class CaseError(Exception):
    """A case file said something this parser will not guess at."""


# =============================================================== the YAML subset
#
# There is no PyYAML on a stock macOS python3, and this repo has no package
# manager, so `import yaml` would make the runner unrunnable for the same
# reason the gated CLI is. What the case files actually use is a small subset:
# scalars, flow sequences, nested maps, lists of maps, and folded blocks.
#
# The rule this parser follows is the repo's own: refuse rather than guess. Any
# construct outside the subset raises CaseError, so a case file can never
# quietly read as half of itself. evals/test-run.py parses every real case file
# in the repo, which is what keeps the subset honest.

_REFUSE = [
    ("&", "an anchor"),
    ("*", "an alias"),
    ("!!", "a tag"),
    ("<<", "a merge key"),
]


def _strip_comment(text):
    """Drop a trailing comment. A '#' only starts one at a line start or after
    a space, and never inside quotes — the same rule that once ate 60
    characters of flow's description."""
    out = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _split_flow(text):
    """Split `[a, b, c]` on commas that are not inside quotes."""
    items = []
    depth = 0
    quote = None
    cur = []
    for ch in text[1:-1]:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        items.append("".join(cur))
    return items


def _unquote(text):
    body = text[1:-1]
    if text[0] == "'":
        return body.replace("''", "'")
    out = []
    i = 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body):
            nxt = body[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(body[i])
            i += 1
    return "".join(out)


def _scalar(text):
    text = text.strip()
    if not text:
        return ""
    if text[0] in "\"'" and len(text) > 1 and text[-1] == text[0]:
        return _unquote(text)
    if text.startswith("[") and text.endswith("]"):
        return [_scalar(x) for x in _split_flow(text)]
    for token, what in _REFUSE:
        if text.startswith(token):
            raise CaseError("%s is outside this parser's subset: %r" % (what, text))
    if text == "|" or text.startswith("|"):
        raise CaseError("a literal block scalar is outside this parser's subset")
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _lines(text):
    out = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        out.append((indent, stripped.strip()))
    return out


def _folded(lines, i, indent):
    """Gather a `>` block: every following line indented past `indent`, joined
    with spaces."""
    parts = []
    while i < len(lines) and lines[i][0] > indent:
        parts.append(lines[i][1])
        i += 1
    return " ".join(parts), i


def _parse_map(lines, i, indent):
    node = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
        text = lines[i][1]
        if ":" not in text:
            raise CaseError("expected `key: value`, got %r" % text)
        key, _, value = text.partition(":")
        key = key.strip()
        value = value.strip()
        i += 1
        if value == ">":
            node[key], i = _folded(lines, i, indent)
        elif value == "":
            if i < len(lines) and lines[i][0] > indent:
                node[key], i = _parse_node(lines, i, lines[i][0])
            else:
                node[key] = None
        else:
            node[key] = _scalar(value)
    return node, i


def _parse_list(lines, i, indent):
    items = []
    while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
        child_indent = indent + 2
        sub = [(child_indent, lines[i][1][2:].strip())]
        i += 1
        while i < len(lines) and lines[i][0] >= child_indent:
            sub.append(lines[i])
            i += 1
        if ":" in sub[0][1] and not sub[0][1].startswith(("\"", "'", "[")):
            item, _ = _parse_map(sub, 0, child_indent)
        else:
            item = _scalar(sub[0][1])
        items.append(item)
    return items, i


def _parse_node(lines, i, indent):
    if lines[i][1].startswith("- "):
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def parse_yaml(text):
    lines = _lines(text)
    if not lines:
        return {}
    node, i = _parse_node(lines, 0, lines[0][0])
    if i != len(lines):
        raise CaseError("could not parse from line %r onward" % (lines[i][1],))
    return node


# ===================================================================== the trace


class Context:
    """What a grader gets to look at."""

    def __init__(self, events, trace, workdir):
        self.events = events
        self.trace = trace
        self.workdir = workdir


def _content(message):
    body = message.get("content")
    if isinstance(body, str):
        return [{"type": "text", "text": body}]
    return body or []


def tool_calls(events):
    """Every tool the assistant invoked, in order."""
    calls = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in _content(event.get("message", {})):
            if block.get("type") == "tool_use":
                calls.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input") or {},
                })
    return calls


def _result_text(block):
    body = block.get("content")
    if isinstance(body, str):
        return body
    if isinstance(body, list):
        return "\n".join(p.get("text", "") for p in body if isinstance(p, dict))
    return ""


def build_trace(events):
    """What the assistant said and did, plus what its tools answered.

    **A rendered SKILL.md is deliberately not in here**, and this is the single
    most load-bearing decision in the file. `Skill` returns the whole skill body
    as a tool result, and `skills/flow/SKILL.md` contains its own worked
    examples — `Quick — single-file copy change.` and `Deep — new subsystem,
    touches auth (danger list).` Count those as trace and three weight-3 graders
    are decided before the model has said one word:

      sizing-quick  / announces-quick    passes on any run that loaded flow
      sizing-quick  / not-sized-heavier  fails on every run, forever
      danger-list   / never-quick        fails on every run, forever

    A skill's body is input to the model, not evidence of what it did. So the
    result of a `Skill` call is dropped and everything else is kept.

    Known limit, stated rather than hidden: a plain `Read` of a SKILL.md would
    land in the trace and could fool a sizing grader the same way. Nothing in
    these cases does that — the scaffolds build a throwaway project that does
    not contain the plugin — but if you write a case that greps the plugin
    source, do not use a bare `regex`/`trace` grader for a size.
    """
    skill_results = {c["id"] for c in tool_calls(events) if c.get("name") == "Skill"}
    parts = []
    for event in events:
        kind = event.get("type")
        if kind == "assistant":
            for block in _content(event.get("message", {})):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(json.dumps(block.get("input") or {}))
        elif kind == "user":
            for block in _content(event.get("message", {})):
                if block.get("type") != "tool_result":
                    continue
                if block.get("tool_use_id") in skill_results:
                    continue
                parts.append(_result_text(block))
    return "\n".join(p for p in parts if p)


# =================================================================== the graders


def _matching_calls(ctx, spec):
    tool = spec.get("tool")
    needle = spec.get("input_match")
    hits = []
    for index, call in enumerate(ctx.events and tool_calls(ctx.events) or []):
        if tool and call.get("name") != tool:
            continue
        if needle and needle not in json.dumps(call.get("input") or {}):
            continue
        hits.append(index)
    return hits


def _grade_tool_used(g, ctx):
    hits = _matching_calls(ctx, g)
    count = len(hits)
    if "min" in g and count < g["min"]:
        return "fail", "%d call(s), wanted at least %d" % (count, g["min"])
    if "max" in g and count > g["max"]:
        return "fail", "%d call(s), wanted at most %d" % (count, g["max"])
    if "min" not in g and "max" not in g:
        return "skip", "neither min nor max given"
    return "pass", "%d call(s)" % count


def _grade_tool_order(g, ctx):
    before = _matching_calls(ctx, g.get("before") or {})
    after = _matching_calls(ctx, g.get("after") or {})
    if not before:
        return "fail", "the `before` call never happened"
    if not after:
        return "fail", "the `after` call never happened"
    if before[0] < after[0]:
        return "pass", "before at #%d, after at #%d" % (before[0], after[0])
    return "fail", "before at #%d came after #%d" % (before[0], after[0])


def _grade_regex(g, ctx):
    target = g.get("target", "trace")
    if isinstance(target, dict) and target.get("source") == "file":
        path = os.path.join(ctx.workdir, target.get("path", ""))
        if not os.path.exists(path):
            # A file the run was supposed to write and did not is a failure of
            # the run, not something this grader cannot judge. `skip` here would
            # quietly excuse the exact thing the case is checking for.
            return "fail", "no such file: %s" % target.get("path")
        with open(path, errors="replace") as fh:
            haystack = fh.read()
    elif target == "trace":
        haystack = ctx.trace
    else:
        return "skip", "unsupported target %r" % (target,)
    found = re.search(g.get("pattern", ""), haystack) is not None
    mode = g.get("match", "contains")
    if mode == "contains":
        return ("pass", "found") if found else ("fail", "not found in the trace")
    if mode == "not_contains":
        return ("fail", "found in the trace") if found else ("pass", "absent")
    return "skip", "unsupported match mode %r" % mode


def _grade_file_exists(g, ctx):
    path = os.path.join(ctx.workdir, g.get("path", ""))
    there = os.path.exists(path)
    want = g.get("exists", True)
    if there == want:
        return "pass", "exists" if there else "absent"
    return "fail", "expected %s, found %s" % (
        "it to exist" if want else "it to be absent",
        "it" if there else "nothing",
    )


GRADERS = {
    "tool_used": _grade_tool_used,
    "tool_order": _grade_tool_order,
    "regex": _grade_regex,
    "file_exists": _grade_file_exists,
}


def grade_one(g, ctx):
    kind = g.get("type")
    if kind == "llm":
        return "skip", "llm grader — needs a judge this runner does not call"
    if kind not in GRADERS:
        return "skip", "unknown grader type %r" % kind
    try:
        return GRADERS[kind](g, ctx)
    except Exception as exc:  # a broken grader is a skip, never a pass
        return "skip", "grader raised %s: %s" % (type(exc).__name__, exc)


def score(results):
    """results: (name, verdict, weight, detail). Skips leave the denominator."""
    earned = sum(w for _, v, w, _ in results if v == "pass")
    scored = sum(w for _, v, w, _ in results if v in ("pass", "fail"))
    skipped = sum(1 for _, v, _, _ in results if v == "skip")
    return {
        "earned": earned,
        "scored": scored,
        "skipped": skipped,
        "ratio": (earned / scored) if scored else 0.0,
        "ok": scored > 0 and earned == scored,
    }


# =================================================================== running one


def load_cases(pattern):
    cases = []
    for name in sorted(os.listdir(HERE)):
        path = os.path.join(HERE, name, "case.yaml")
        if not os.path.isfile(path):
            continue
        if pattern and not fnmatch.fnmatch(name, pattern):
            continue
        with open(path) as fh:
            doc = parse_yaml(fh.read())
        doc["_dir"] = os.path.join(HERE, name)
        doc.setdefault("name", name)
        cases.append(doc)
    return cases


def scaffold(case, workdir):
    script = (case.get("context") or {}).get("scaffold_script")
    if not script:
        return
    path = os.path.normpath(os.path.join(case["_dir"], script))
    done = subprocess.run(["bash", path, workdir], capture_output=True, text=True)
    if done.returncode != 0:
        raise CaseError("scaffold failed (exit %d):\n%s" % (done.returncode, done.stderr.strip()))


def run_once(case, workdir, permission_mode):
    ex = case.get("execution") or {}
    cmd = [
        "claude", "-p", ex.get("prompt", ""),
        "--plugin-dir", PLUGIN_ROOT,
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", permission_mode,
    ]
    if ex.get("max_turns"):
        cmd += ["--max-turns", str(ex["max_turns"])]
    if ex.get("allowed_tools"):
        cmd += ["--allowedTools"] + list(ex["allowed_tools"])

    done = subprocess.run(
        cmd, cwd=workdir, capture_output=True, text=True,
        timeout=ex.get("timeout_seconds", 900),
    )
    events = []
    for line in done.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not events:
        raise CaseError(
            "no stream-json events came back (exit %d).\nstdout: %s\nstderr: %s"
            % (done.returncode, done.stdout[:400], done.stderr[:400])
        )
    return events


def run_case(case, runs, permission_mode, keep_temp):
    ex = case.get("execution") or {}
    graders = case.get("graders") or []
    print("\n=== %s  (%d run%s, %d graders)" % (
        case["name"], runs, "" if runs == 1 else "s", len(graders)))
    print("    %s" % ex.get("prompt", "")[:100])

    run_scores = []
    for n in range(runs):
        workdir = tempfile.mkdtemp(prefix="devflow-eval-")
        try:
            scaffold(case, workdir)
            events = run_once(case, workdir, permission_mode)
            ctx = Context(events, build_trace(events), workdir)
            results = []
            for g in graders:
                verdict, detail = grade_one(g, ctx)
                results.append((g.get("name", "?"), verdict, g.get("weight", 1), detail))
            s = score(results)
            run_scores.append(s)
            mark = "PASS" if s["ok"] else "FAIL"
            print("  run %d: %s  %d/%d weighted, %d skipped" % (
                n + 1, mark, s["earned"], s["scored"], s["skipped"]))
            for name, verdict, weight, detail in results:
                glyph = {"pass": "ok  ", "fail": "FAIL", "skip": "skip"}[verdict]
                print("    %s %-38s w=%d  %s" % (glyph, name, weight, detail))
        except Exception as exc:
            print("  run %d: ERROR  %s" % (n + 1, exc))
            run_scores.append({"ok": False, "earned": 0, "scored": 0, "skipped": 0})
        finally:
            if keep_temp:
                print("    kept: %s" % workdir)
            else:
                shutil.rmtree(workdir, ignore_errors=True)
    return run_scores


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--case", help="glob over case directory names")
    ap.add_argument("--runs", type=int, help="override each case's `runs`")
    ap.add_argument("--permission-mode", default="default")
    ap.add_argument("--keep-temp", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse the cases and print them; run nothing")
    args = ap.parse_args()

    cases = load_cases(args.case)
    if not cases:
        print("no cases matched %r" % args.case)
        return 1

    if args.dry_run:
        for case in cases:
            graders = case.get("graders") or []
            free = [g for g in graders if g.get("type") in GRADERS]
            print("%-22s %2d graders, %2d scorable here, %2d llm/skipped"
                  % (case["name"], len(graders), len(free), len(graders) - len(free)))
        return 0

    if not shutil.which("claude"):
        print("no `claude` on PATH — this runner drives the CLI")
        return 1

    failed = []
    for case in cases:
        runs = args.runs or case.get("runs", 3)
        scores = run_case(case, runs, args.permission_mode, args.keep_temp)
        if not all(s["ok"] for s in scores):
            failed.append(case["name"])

    total_skipped = 0
    for case in cases:
        total_skipped += sum(1 for g in (case.get("graders") or [])
                             if g.get("type") not in GRADERS)

    print("\n" + "-" * 60)
    if failed:
        print("FAILED: %s" % ", ".join(failed))
    else:
        print("all cases passed the graders this runner scores")
    print("%d llm grader(s) were NOT run and are NOT counted as passed." % total_skipped)
    print("`claude plugin eval` scores those; it is gated behind early access.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
