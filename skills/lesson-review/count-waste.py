#!/usr/bin/env python3
"""Count waste from saved Claude Code sessions.

    python3 skills/lesson-review/count-waste.py [--projects-dir DIR] [--since YYYY-MM-DD] [--json]

Why these numbers, and why they are collected this way: docs/lessons.md.

Claude Code already saves every session under `~/.claude/projects/<project>/
<session-uuid>.jsonl`, one JSON object per line, and a subagent's own
transcript is saved beside its parent session, at
`<project>/<session-uuid>/subagents/agent-*.jsonl` with a sibling
`.meta.json` naming its `agentType`. None of this is documented -- it is
read off a real directory, not a spec -- so this script skips whatever line
it cannot make sense of and counts the skips, rather than guessing a shape
and crashing on the next Claude Code release that changes it.

What is counted, per devflow skill:

- how often a human replied "yes to all", charged to whichever skill's
  command was open when they said it
- permission prompts -- but the session file only ever records a *denial*
  (`toolDenialKind`); an approved prompt leaves no trace at all, so
  approvals are always reported as `"not recorded"` rather than guessed at
- each `flow` run's size (its "Quick/Standard/Deep — ..." line) alongside
  the whole session's duration and cost, taken from that session's last
  `cost-state` record -- the file only totals a session, never a single run,
  so a session with more than one `flow` run in it gets that same session
  total attached to each of its runs
- how many `review` runs happened, and how many of them reported no
  findings, matched by a short, best-effort list of phrases `review`'s own
  SKILL.md uses for a clean run -- there is no single marker Claude Code
  guarantees, so this is a text match, not a hard contract
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

SIZE_RE = re.compile(r"^(Quick|Standard|Deep)\s+—")
COMMAND_NAME_RE = re.compile(r"<command-name>\s*/?([^<]+?)\s*</command-name>")

# Best-effort. `review`'s SKILL.md prints one of these when an axis found
# nothing to raise. See docs/lessons.md for why this cannot be a hard match.
NO_FINDINGS_MARKERS = (
    "nothing to challenge",
    "nothing to review since",
    "no findings",
    "found nothing",
)


def normalize_skill(name):
    """`/devflow:review` and the bare `/flow` both name a devflow skill;
    fold them to the same `devflow:<name>` key."""
    name = name.strip().lstrip("/")
    if not name:
        return None
    if name.startswith("devflow:"):
        return name
    return "devflow:" + name


def text_blocks(content):
    """Yield every readable string out of a `message.content` value,
    whatever shape it came in -- a plain string, or a list of blocks
    (text, tool_result, tool_use)."""
    if isinstance(content, str):
        yield content
        return
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text" and isinstance(block.get("text"), str):
            yield block["text"]
        elif btype == "tool_result":
            inner = block.get("content")
            if isinstance(inner, str):
                yield inner
            elif isinstance(inner, list):
                for sub in inner:
                    if isinstance(sub, dict) and sub.get("type") == "text":
                        yield sub.get("text", "")


def skill_tool_uses(content):
    """Yield each `skill` a `Skill` tool_use block named."""
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
            skill = (block.get("input") or {}).get("skill")
            if skill:
                yield skill


def record_timestamp(rec):
    ts = rec.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_jsonl(path):
    """Yield each parsed record. A line, or a whole file, that cannot be
    read counts as skipped rather than raising."""
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        yield ("skip", None)
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                yield ("skip", None)
                continue
            if not isinstance(rec, dict):
                yield ("skip", None)
                continue
            yield ("rec", rec)


def process_records(records, seed_skill=None):
    """Walk one session's (or one subagent's) records in order and return
    its local tallies. `seed_skill` is the skill to charge events to before
    anything in the file says otherwise -- a subagent's own `agentType`."""
    stats = {
        "yes_to_all": {},
        "denials": {},
        "flow_runs": [],
        "review": {},  # skill -> [runs, no_findings]
        "skipped": 0,
        "last_timestamp": None,
        "cost_state": None,
    }
    current_skill = seed_skill
    review_run = None  # [skill, found_nothing] while a review run is open

    def close_review():
        nonlocal review_run
        if review_run is None:
            return
        skill, found = review_run
        r = stats["review"].setdefault(skill, [0, 0])
        r[0] += 1
        if found:
            r[1] += 1
        review_run = None

    for kind, rec in records:
        if kind == "skip":
            stats["skipped"] += 1
            continue

        ts = record_timestamp(rec)
        if ts is not None:
            stats["last_timestamp"] = ts

        if rec.get("type") == "cost-state":
            stats["cost_state"] = rec
            continue

        message = rec.get("message")
        content = message.get("content") if isinstance(message, dict) else None

        if isinstance(content, str):
            m = COMMAND_NAME_RE.search(content)
            if m:
                new_skill = normalize_skill(m.group(1))
                if new_skill and new_skill != current_skill:
                    close_review()
                    current_skill = new_skill
                    if new_skill == "devflow:review":
                        review_run = [new_skill, False]

        attribution = rec.get("attributionSkill")
        if attribution:
            current_skill = attribution

        for used in skill_tool_uses(content):
            current_skill = used

        if isinstance(content, str) and content.strip().lower() == "yes to all":
            origin = rec.get("origin") or {}
            if origin.get("kind") == "human" and current_skill:
                stats["yes_to_all"][current_skill] = stats["yes_to_all"].get(current_skill, 0) + 1

        denial_kind = rec.get("toolDenialKind")
        if denial_kind and current_skill:
            d = stats["denials"].setdefault(current_skill, {})
            d[denial_kind] = d.get(denial_kind, 0) + 1

        for text in text_blocks(content):
            stripped = text.strip()
            m = SIZE_RE.match(stripped)
            if m and current_skill == "devflow:flow":
                stats["flow_runs"].append({"size": m.group(1)})
            if review_run is not None:
                low = text.lower()
                if any(marker in low for marker in NO_FINDINGS_MARKERS):
                    review_run[1] = True

    close_review()
    return stats


def find_sessions(projects_dir):
    """Yield (session_id, session_jsonl_path, [subagent_jsonl_paths])."""
    pattern = os.path.join(projects_dir, "*", "*.jsonl")
    for path in sorted(glob.glob(pattern)):
        if os.path.sep + "subagents" + os.path.sep in path:
            continue  # reached directly from its session below, not here
        if not os.path.isfile(path):
            continue
        session_id = os.path.basename(path)[: -len(".jsonl")]
        session_dir = path[: -len(".jsonl")]
        sub_glob = os.path.join(session_dir, "subagents", "*.jsonl")
        subagents = sorted(glob.glob(sub_glob))
        yield session_id, path, subagents


def subagent_type(subagent_path):
    meta_path = subagent_path[: -len(".jsonl")] + ".meta.json"
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        agent_type = meta.get("agentType")
        if agent_type:
            return agent_type
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return "unknown-subagent"


def merge_counts(target, source):
    for skill, count in source.items():
        target[skill] = target.get(skill, 0) + count


def merge_denials(target, source):
    for skill, kinds in source.items():
        d = target.setdefault(skill, {})
        for kind, count in kinds.items():
            d[kind] = d.get(kind, 0) + count


def merge_review(target, source):
    for skill, (runs, no_findings) in source.items():
        r = target.setdefault(skill, [0, 0])
        r[0] += runs
        r[1] += no_findings


def scan(projects_dir, since=None):
    """Read every session under `projects_dir` and return the report dict.
    `since` is a `YYYY-MM-DD` string, or `None` for no cutoff."""
    since_dt = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    report = {
        "sessions_scanned": 0,
        "skipped_lines": 0,
        "yes_to_all": {},
        "denials": {},
        "approvals": "not recorded",
        "flow_runs": [],
        "review_runs": {},
    }

    if not os.path.isdir(projects_dir):
        return report

    for session_id, session_path, subagent_paths in find_sessions(projects_dir):
        session_stats = process_records(read_jsonl(session_path))

        if since_dt is not None:
            last = session_stats["last_timestamp"]
            if last is not None and last < since_dt:
                continue

        report["sessions_scanned"] += 1
        report["skipped_lines"] += session_stats["skipped"]
        merge_counts(report["yes_to_all"], session_stats["yes_to_all"])
        merge_denials(report["denials"], session_stats["denials"])
        merge_review(report["review_runs"], session_stats["review"])

        cost_state = session_stats["cost_state"] or {}
        duration_ms = cost_state.get("totalDuration")
        cost_usd = cost_state.get("totalCostUSD")
        for run in session_stats["flow_runs"]:
            report["flow_runs"].append(
                {
                    "size": run["size"],
                    "session": session_id,
                    "duration_ms": duration_ms,
                    "cost_usd": cost_usd,
                }
            )

        for subagent_path in subagent_paths:
            agent_type = subagent_type(subagent_path)
            sub_stats = process_records(read_jsonl(subagent_path), seed_skill=agent_type)
            report["skipped_lines"] += sub_stats["skipped"]
            merge_counts(report["yes_to_all"], sub_stats["yes_to_all"])
            merge_denials(report["denials"], sub_stats["denials"])

    report["review_runs"] = {
        skill: {"runs": runs, "no_findings": no_findings}
        for skill, (runs, no_findings) in report["review_runs"].items()
    }
    return report


def render_plain(report):
    lines = []
    lines.append(
        f"count-waste: {report['sessions_scanned']} sessions scanned, "
        f"{report['skipped_lines']} unparsable lines skipped"
    )
    lines.append("")

    lines.append('yes to all (charged to the skill whose command was open)')
    if report["yes_to_all"]:
        for skill in sorted(report["yes_to_all"]):
            lines.append(f"  {skill}: {report['yes_to_all'][skill]}")
    else:
        lines.append("  none")
    lines.append("")

    lines.append("permission prompts (only what the session file records)")
    if report["denials"]:
        for skill in sorted(report["denials"]):
            kinds = ", ".join(f"{k}: {v}" for k, v in sorted(report["denials"][skill].items()))
            lines.append(f"  {skill} denied - {kinds}")
    else:
        lines.append("  no denials recorded")
    lines.append(f"  approvals: {report['approvals']}")
    lines.append("")

    lines.append("flow runs (size, then that session's duration and cost)")
    if report["flow_runs"]:
        for run in report["flow_runs"]:
            duration = run["duration_ms"]
            cost = run["cost_usd"]
            duration_s = "not recorded" if duration is None else f"{duration / 1000:.1f}s"
            cost_s = "not recorded" if cost is None else f"${cost:.2f}"
            lines.append(f"  {run['size']:<8} session {run['session']}  {duration_s}  {cost_s}")
    else:
        lines.append("  none")
    lines.append("")

    lines.append("review runs, and how many reported no findings")
    if report["review_runs"]:
        for skill in sorted(report["review_runs"]):
            r = report["review_runs"][skill]
            lines.append(f"  {skill}: {r['runs']} runs, {r['no_findings']} found nothing")
    else:
        lines.append("  none")

    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--projects-dir",
        default=os.path.expanduser("~/.claude/projects"),
        help="defaults to ~/.claude/projects",
    )
    parser.add_argument("--since", default=None, help="YYYY-MM-DD, only sessions on or after this date")
    parser.add_argument("--json", action="store_true", help="print the machine-readable report instead")
    args = parser.parse_args(argv)

    report = scan(args.projects_dir, since=args.since)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_plain(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
