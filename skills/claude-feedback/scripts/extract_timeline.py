#!/usr/bin/env python3
"""Extract a compact, chronological digest of a Claude Code session transcript.

The digest is an INTERMEDIATE artifact for Claude to reason over in-session.
It still contains raw (potentially sensitive) content — it must NEVER be
included verbatim in the feedback report. The sanitization happens when
Claude writes the report, per SKILL.md.

Usage:
  python3 extract_timeline.py                    # newest session for cwd
  python3 extract_timeline.py --session <prefix> # session id prefix match
  python3 extract_timeline.py --path <file.jsonl>
  python3 extract_timeline.py --list             # list recent sessions for cwd
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
TRUNC = 300


def project_dir_for_cwd(cwd: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9-]", "-", cwd)
    return os.path.join(PROJECTS_DIR, slug)


def list_sessions(pdir: str):
    if not os.path.isdir(pdir):
        return []
    files = [os.path.join(pdir, f) for f in os.listdir(pdir) if f.endswith(".jsonl")]
    return sorted(files, key=os.path.getmtime, reverse=True)


def trunc(text, n=TRUNC):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[:n] + f"… [+{len(text) - n} chars]"


def fmt_ts(ts):
    if not ts:
        return "??:??:??"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M:%S")
    except ValueError:
        return ts


def tool_input_summary(name, inp):
    if not isinstance(inp, dict):
        return trunc(inp, 120)
    if name == "Bash":
        return trunc(inp.get("command", ""), 200)
    for key in ("file_path", "path", "notebook_path"):
        if key in inp:
            extra = ""
            if "old_string" in inp:
                extra = f" (edit, {len(str(inp['old_string']))}→{len(str(inp.get('new_string', '')))} chars)"
            elif "content" in inp:
                extra = f" (write, {len(str(inp['content']))} chars)"
            return inp[key] + extra
    if name in ("Grep", "Glob"):
        return trunc(json.dumps({k: v for k, v in inp.items() if k in ("pattern", "path", "glob", "output_mode")}), 200)
    if name in ("Task", "Agent"):
        return f"[{inp.get('subagent_type', 'agent')}] {trunc(inp.get('prompt', inp.get('description', '')), 200)}"
    return trunc(json.dumps(inp), 200)


def content_blocks(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path")
    ap.add_argument("--session")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cwd", default=os.getcwd())
    args = ap.parse_args()

    pdir = project_dir_for_cwd(args.cwd)
    sessions = list_sessions(pdir)

    if args.list:
        for f in sessions[:15]:
            mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M")
            print(f"{mtime}  {os.path.basename(f)}")
        return

    if args.path:
        path = args.path
    elif args.session:
        matches = [f for f in sessions if os.path.basename(f).startswith(args.session)]
        if not matches:
            sys.exit(f"No session matching '{args.session}' in {pdir}")
        path = matches[0]
    else:
        if not sessions:
            sys.exit(f"No transcripts found in {pdir}")
        path = sessions[0]

    meta = {"session": os.path.basename(path).replace(".jsonl", ""), "versions": set(),
            "models": set(), "cwds": set(), "branches": set(), "modes": set()}
    counts = {"user_prompts": 0, "assistant_msgs": 0, "tool_calls": 0,
              "tool_errors": 0, "sidechain_events": 0, "compactions": 0}
    first_ts = last_ts = None
    events = []
    tool_names = {}  # tool_use id -> name, to label results

    with open(path) as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = o.get("type")
            ts = o.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
            for field, key in (("version", "versions"), ("cwd", "cwds"),
                               ("gitBranch", "branches"), ("permissionMode", "modes")):
                if o.get(field):
                    meta[key].add(o[field])

            if o.get("isSidechain"):
                counts["sidechain_events"] += 1
                continue

            if t == "user":
                msg = o.get("message", {})
                blocks = content_blocks(msg)
                for b in blocks:
                    if b.get("type") == "tool_result":
                        raw = b.get("content")
                        if isinstance(raw, list):
                            raw = " ".join(x.get("text", "") for x in raw if isinstance(x, dict))
                        is_err = bool(b.get("is_error")) or str(raw).startswith("Exit code")
                        if is_err:
                            counts["tool_errors"] += 1
                        name = tool_names.get(b.get("tool_use_id"), "?")
                        flag = " ERROR" if is_err else ""
                        events.append(f"{fmt_ts(ts)}  ⤷ result[{name}]{flag} ({len(str(raw))} chars): {trunc(raw, 200)}")
                    elif b.get("type") == "text" and not o.get("isMeta"):
                        txt = b.get("text", "")
                        if txt.startswith(("<local-command", "<command-name>", "<system-reminder")):
                            m = re.search(r"<command-name>(.*?)</command-name>", txt)
                            if m:
                                events.append(f"{fmt_ts(ts)}  USER ran command: {m.group(1)}")
                            continue
                        counts["user_prompts"] += 1
                        events.append(f"{fmt_ts(ts)}  USER: {trunc(txt)}")
                    elif b.get("type") == "image":
                        events.append(f"{fmt_ts(ts)}  USER: [pasted an image]")

            elif t == "assistant":
                msg = o.get("message", {})
                if msg.get("model"):
                    meta["models"].add(msg["model"])
                for b in content_blocks(msg):
                    bt = b.get("type")
                    if bt == "text" and b.get("text", "").strip():
                        counts["assistant_msgs"] += 1
                        events.append(f"{fmt_ts(ts)}  CLAUDE: {trunc(b['text'])}")
                    elif bt == "tool_use":
                        counts["tool_calls"] += 1
                        tool_names[b.get("id")] = b.get("name")
                        events.append(f"{fmt_ts(ts)}  → {b.get('name')}: {tool_input_summary(b.get('name'), b.get('input'))}")

            elif t == "system":
                sub = o.get("subtype", "")
                if "compact" in sub.lower():
                    counts["compactions"] += 1
                    events.append(f"{fmt_ts(ts)}  [SYSTEM] context compaction ({sub})")
                elif o.get("hookErrors"):
                    events.append(f"{fmt_ts(ts)}  [SYSTEM] hook errors: {trunc(o['hookErrors'], 200)}")
                elif o.get("level") == "error" or sub == "api_error":
                    events.append(f"{fmt_ts(ts)}  [SYSTEM:{sub}] {trunc(o.get('content', json.dumps(o)), 200)}")

    dur = ""
    if first_ts and last_ts:
        try:
            d1 = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            d2 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            dur = str(d2 - d1).split(".")[0]
        except ValueError:
            pass

    print("=== SESSION DIGEST (raw — do NOT paste into the report) ===")
    print(f"session:   {meta['session']}")
    print(f"cc_version:{','.join(sorted(meta['versions']))}")
    print(f"models:    {','.join(sorted(meta['models']))}")
    print(f"perm_mode: {','.join(sorted(meta['modes']))}")
    print(f"cwd:       {','.join(sorted(meta['cwds']))}   [SENSITIVE — generalize]")
    print(f"branch:    {','.join(sorted(meta['branches']))}   [SENSITIVE — generalize]")
    print(f"started:   {first_ts}   ended: {last_ts}   duration: {dur}")
    print(f"counts:    {json.dumps(counts)}")
    print(f"platform:  {sys.platform}")
    print("=== TIMELINE ===")
    for e in events:
        print(e)


if __name__ == "__main__":
    main()
