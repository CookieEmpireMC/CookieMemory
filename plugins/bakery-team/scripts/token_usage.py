#!/usr/bin/env python3
"""Token usage per agent, per feature and per repo for the Cookie Empire team (standard library only).

Claude Code writes every session to ~/.claude/projects/<project>/<session>.jsonl and every subagent to
<session>/subagents/agent-<id>.jsonl (+ .meta.json with its agent type). This script sums the API usage in
those transcripts and keeps the totals in a ledger, so they survive Claude Code's transcript cleanup.

    token_usage.py --hook                    SubagentStop / SessionEnd hook: record the session from stdin
    token_usage.py record                    record every Cookie Empire session on this machine
    token_usage.py report [--feature NAME] [--repo NAME] [--since YYYY-MM-DD] [--by agent|feature|run]

Ledger: ${XDG_STATE_HOME:-~/.local/state}/cookie-empire/token-usage.json (one row per run, per machine).
Tokens: "input" is uncached input, "cache write"/"cache read" are prompt-cache tokens, "output" includes thinking.
"Weighted" = input + 1.25 x cache write + 0.1 x cache read + 5 x output: the same relative weights as the API's
price list for every Claude model, so it ranks cost within one model. Across models also compare the model
column (opus costs more per token than sonnet, sonnet more than haiku).
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

PROJECTS = os.path.expanduser("~/.claude/projects")
LEDGER = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
                      "cookie-empire", "token-usage.json")
REPOS = ("CookieClicker", "CookieCore", "CookieMemory")
FEATURE_IN_PROMPT = re.compile(r"[Ff]eature `([\w.-]+)`")
FIELDS = ("input", "cache_write", "cache_read", "output")


def repo_of(cwd):
    parts = (cwd or "").split(os.sep)
    if ".claude" in parts:  # agent worktree: <repo>/.claude/worktrees/agent-…
        parts = parts[:parts.index(".claude")]
    name = parts[-1] if parts else ""
    return name if name in REPOS else None


def first_prompt(entries):
    for e in entries:
        if e.get("type") == "user":
            c = (e.get("message") or {}).get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return " ".join(b.get("text", "") for b in c if isinstance(b, dict))
    return ""


def feature_of_branch(branch):
    return branch[8:] if branch and branch.startswith("feature/") else None


def summarise(path, agent, description="", split_by_branch=False):
    """Runs from one transcript: one run, or (main session) one run per feature branch it worked on."""
    entries = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except ValueError:
                pass
    # One API response is logged once per content block, and the usage grows while it streams:
    # keep the last usage per message id, count tool_use blocks across all of them.
    usage, order, tools, models, times = {}, [], defaultdict(int), {}, defaultdict(list)
    cwd, branch = None, None
    for e in entries:
        cwd = cwd or e.get("cwd")
        branch = e.get("gitBranch") or branch
        msg = e.get("message")
        if e.get("type") != "assistant" or not isinstance(msg, dict) or not msg.get("usage"):
            continue
        key = msg.get("id") or e.get("requestId") or e.get("uuid")
        if key not in usage:
            order.append((key, branch))
        usage[key] = msg["usage"]
        models[key] = msg.get("model") or "?"
        if e.get("timestamp"):
            times[key].append(e["timestamp"])
        if isinstance(msg.get("content"), list):
            tools[key] += sum(1 for b in msg["content"] if isinstance(b, dict) and b.get("type") == "tool_use")
    if not order:
        return []
    prompt = first_prompt(entries)
    m = FEATURE_IN_PROMPT.search(prompt) or FEATURE_IN_PROMPT.search(description)
    fixed = m.group(1) if m else None
    runs = {}
    for key, br in order:
        feature = (feature_of_branch(br) or "-") if split_by_branch else (fixed or feature_of_branch(br) or "-")
        r = runs.setdefault(feature, {"repo": repo_of(cwd), "feature": feature, "agent": agent,
                                      "description": description, "models": defaultdict(int), "calls": 0,
                                      "tool_uses": 0, "start": "", "end": "", **dict.fromkeys(FIELDS, 0)})
        u = usage[key]
        r["input"] += u.get("input_tokens") or 0
        r["cache_write"] += u.get("cache_creation_input_tokens") or 0
        r["cache_read"] += u.get("cache_read_input_tokens") or 0
        r["output"] += u.get("output_tokens") or 0
        r["calls"] += 1
        r["tool_uses"] += tools[key]
        r["models"][models[key]] += 1
        for t in times[key]:
            r["start"] = min(r["start"] or t, t)
            r["end"] = max(r["end"], t)
    for r in runs.values():
        r["model"] = max(r["models"], key=r["models"].get)
        del r["models"]
    return list(runs.values())


def session_runs(main_transcript):
    """(run id, summary) for a main session and all of its subagents."""
    sid = os.path.splitext(os.path.basename(main_transcript))[0]
    if os.path.exists(main_transcript):
        for s in summarise(main_transcript, "orchestrator", split_by_branch=True):
            if s["repo"]:
                yield f"{sid}:main:{s['feature']}", s
    for path in glob.glob(os.path.join(os.path.dirname(main_transcript), sid, "subagents", "agent-*.jsonl")):
        aid = os.path.basename(path)[6:-6]
        try:
            meta = json.load(open(path[:-6] + ".meta.json"))
        except (OSError, ValueError):
            meta = {}
        agent = (meta.get("agentType") or "general-purpose").removeprefix("bakery-team:")
        for s in summarise(path, agent, meta.get("description") or ""):
            if s["repo"]:
                yield f"{sid}:{aid}", s


def load_ledger():
    try:
        return json.load(open(LEDGER))
    except (OSError, ValueError):
        return {}


def save_ledger(ledger):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    tmp = LEDGER + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ledger, f, indent=0)
    os.replace(tmp, LEDGER)


def record(transcripts):
    ledger = load_ledger()
    for t in transcripts:
        for rid, s in session_runs(t):
            ledger[rid] = s  # a resumed agent keeps growing: always overwrite with the full total
    save_ledger(ledger)
    return ledger


def all_transcripts():
    return glob.glob(os.path.join(PROJECTS, "*", "*.jsonl"))


def weighted(g):
    return g["input"] + 1.25 * g["cache_write"] + 0.1 * g["cache_read"] + 5 * g["output"]


def fmt(n):
    n = round(n)
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def report(args):
    rows = [r for r in record(all_transcripts()).values()
            if (not args.repo or r["repo"] == args.repo) and (not args.feature or r["feature"] == args.feature)
            and (not args.since or r["start"][:10] >= args.since)]
    if not rows:
        print("No token usage recorded for that filter.")
        return
    key = {"agent": lambda r: (r["agent"],), "feature": lambda r: (r["repo"], r["feature"]),
           "run": lambda r: (r["feature"], r["agent"], r["description"] or r["start"][:16])}[args.by]
    groups = defaultdict(lambda: dict.fromkeys(FIELDS + ("runs", "calls", "tool_uses"), 0))
    models = defaultdict(set)
    for r in rows:
        g = groups[key(r)]
        g["runs"] += 1
        for f in FIELDS + ("calls", "tool_uses"):
            g[f] += r[f]
        models[key(r)].add(r["model"].removeprefix("claude-"))
    head = {"agent": "Agent", "feature": "Repo · feature", "run": "Feature · agent · run"}[args.by]
    print(f"| {head} | Model | Runs | API calls | Tool uses | Input | Cache write | Cache read | Output | Total | Weighted | Cache hit |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    total = dict.fromkeys(FIELDS, 0)
    for k, g in sorted(groups.items(), key=lambda kv: -weighted(kv[1])):
        t = sum(g[f] for f in FIELDS)
        prompt = g["input"] + g["cache_write"] + g["cache_read"]
        hit = f"{100 * g['cache_read'] / prompt:.0f}%" if prompt else "-"
        print(f"| {' · '.join(k)} | {', '.join(sorted(models[k]))} | {g['runs']} | {g['calls']} | {g['tool_uses']} | "
              f"{fmt(g['input'])} | {fmt(g['cache_write'])} | {fmt(g['cache_read'])} | {fmt(g['output'])} | "
              f"{fmt(t)} | {fmt(weighted(g))} | {hit} |")
        for f in FIELDS:
            total[f] += g[f]
    print(f"| **Total** | | {len(rows)} | | | {fmt(total['input'])} | {fmt(total['cache_write'])} | "
          f"{fmt(total['cache_read'])} | {fmt(total['output'])} | {fmt(sum(total.values()))} | **{fmt(weighted(total))}** | |")


def main():
    if "--hook" in sys.argv:
        try:
            data = json.load(sys.stdin)
            if data.get("transcript_path"):
                record([data["transcript_path"]])
        except Exception:
            pass  # never get in the way of a session
        return
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("record")
    r = sub.add_parser("report")
    r.add_argument("--feature")
    r.add_argument("--repo")
    r.add_argument("--since")
    r.add_argument("--by", choices=("agent", "feature", "run"), default="agent")
    args = p.parse_args()
    if args.cmd == "record":
        print(f"{len(record(all_transcripts()))} run(s) in {LEDGER}")
    else:
        report(args)


if __name__ == "__main__":
    main()
