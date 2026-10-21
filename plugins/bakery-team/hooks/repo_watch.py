#!/usr/bin/env python3
"""Repo watch: fetch every Cookie Empire repo on this machine, report what was pushed since you last looked,
and fast-forward local branches that are simply behind (standard library only).

Runs as a SessionStart hook (default: JSON for Claude Code) or by hand / from the repo-watcher agent:
    python3 repo_watch.py --text      # human-readable report
    python3 repo_watch.py --peek      # report without marking anything as seen

Repos: every git repo next to the current project (or in $COOKIE_EMPIRE_DIR) whose origin is on
github.com/CookieEmpireMC. What you have seen is kept per machine in
${XDG_STATE_HOME:-~/.local/state}/cookie-empire/repo-watch.json.
Fast-forward only: a branch with local commits, or checked out in a worktree with uncommitted changes,
is never touched, only reported.
"""
import json, os, subprocess, sys

ORG = "CookieEmpireMC/"
MAX_COMMITS = 8
STATE = os.path.join(os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
                     "cookie-empire", "repo-watch.json")


def git(repo, *args, timeout=20):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip()


def find_repos():
    base = os.environ.get("COOKIE_EMPIRE_DIR") or os.path.dirname(
        os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    repos = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        _, url = git(path, "remote", "get-url", "origin")
        if ORG.lower() in url.lower():
            repos.append((name, path))
    return repos


def remote_heads(repo):
    _, out = git(repo, "for-each-ref", "--format=%(refname:strip=3) %(objectname)", "refs/remotes/origin")
    return dict(line.split(" ", 1) for line in out.splitlines() if line and not line.startswith("HEAD "))


def new_commits(repo, old, new):
    rng = f"{old}..{new}" if old else new
    _, out = git(repo, "log", "--no-merges", f"--max-count={MAX_COMMITS + 1}", "--format=%h %an: %s", rng)
    lines = out.splitlines()
    more = len(lines) > MAX_COMMITS
    _, merges = git(repo, "log", "--merges", "--max-count=5", "--format=%h %s", rng) if old else (0, "")
    return lines[:MAX_COMMITS], more, merges.splitlines()


def worktrees(repo):
    """branch -> worktree path, for every checked-out branch."""
    _, out = git(repo, "worktree", "list", "--porcelain")
    result, path = {}, None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[9:]
        elif line.startswith("branch refs/heads/"):
            result[line[18:]] = path
    return result


def fast_forward(repo):
    """Fast-forward every local branch that tracks origin and is only behind. Returns report lines."""
    notes = []
    _, out = git(repo, "for-each-ref", "--format=%(refname:strip=2) %(upstream:short)", "refs/heads")
    checked_out = worktrees(repo)
    for line in out.splitlines():
        branch, _, upstream = line.partition(" ")
        if not upstream.startswith("origin/"):
            continue
        code, counts = git(repo, "rev-list", "--left-right", "--count", f"{branch}...{upstream}")
        if code:
            continue
        ahead, behind = map(int, counts.split())
        if not behind:
            continue
        if ahead:
            notes.append(f"{branch}: {ahead} local and {behind} new remote commit(s), not merged (diverged)")
            continue
        wt = checked_out.get(branch)
        if wt:
            _, dirty = git(wt, "status", "--porcelain", "--untracked-files=no")
            if dirty:
                notes.append(f"{branch}: {behind} commit(s) behind, not pulled (uncommitted changes in {wt})")
                continue
            code, _ = git(wt, "merge", "--ff-only", "-q", upstream)
        else:
            _, new = git(repo, "rev-parse", upstream)
            _, old = git(repo, "rev-parse", branch)
            code, _ = git(repo, "update-ref", f"refs/heads/{branch}", new, old)
        notes.append(f"{branch}: pulled {behind} commit(s)" if not code else f"{branch}: fast-forward failed")
    return notes


def main():
    peek = "--peek" in sys.argv
    text = "--text" in sys.argv or peek
    try:
        state = json.load(open(STATE))
    except (OSError, ValueError):
        state = {}
    first_run = not state
    sections, fetch_errors, plugin_changed = [], [], False

    for name, path in find_repos():
        try:
            code, _ = git(path, "fetch", "--quiet", "--prune", "origin", timeout=30)
        except subprocess.TimeoutExpired:
            code = 1
        if code:
            fetch_errors.append(name)
        heads = remote_heads(path)
        seen = state.get(name, {})
        lines = []
        for branch, sha in sorted(heads.items()):
            if seen.get(branch) == sha or first_run:
                continue
            commits, more, merges = new_commits(path, seen.get(branch), sha)
            if not commits and not merges:
                continue
            label = "new branch" if branch not in seen else "updated"
            lines.append(f"  {branch} ({label})")
            lines += [f"    {c}" for c in commits]
            if more:
                lines.append("    …")
            lines += [f"    merged: {m}" for m in merges]
            if name == "CookieMemory" and branch == "main":
                plugin_changed = True
        gone = sorted(set(seen) - set(heads))
        if gone and not first_run:
            lines.append(f"  deleted on GitHub: {', '.join(gone)}")
        ff = fast_forward(path) if not peek else []
        lines += [f"  local {n}" for n in ff]
        if lines:
            sections.append(f"{name}:\n" + "\n".join(lines))
        if not peek:
            state[name] = heads

    if not peek:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w") as f:
            json.dump(state, f, indent=1)

    if first_run and not peek:
        summary = f"Repo watch: now watching {len(state)} Cookie Empire repo(s); you'll hear about new pushes from now on."
    elif sections:
        summary = "Repo watch: new pushes in " + ", ".join(s.split(":", 1)[0] for s in sections) + "."
    else:
        summary = ""
    if plugin_changed:
        summary += (" CookieMemory main changed: the bakery-team plugin updates on the next session"
                    " (or now: /plugin marketplace update cookie-memory, then /reload-plugins).")
    if fetch_errors:
        summary += f" Couldn't fetch: {', '.join(fetch_errors)}."
    detail = "\n".join(sections)

    if text:
        print(summary.strip() or "Repo watch: nothing new.")
        if detail:
            print(detail)
        return
    if not summary:
        return
    out = {"systemMessage": summary.strip()}
    if detail:
        out["systemMessage"] += "\n" + detail
        out["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": "Other Cookie Empire repos changed since the user's last session (already "
                                 "fetched; local branches fast-forwarded where safe). Mention it if it affects "
                                 "the current work:\n" + detail,
        }
    print(json.dumps(out))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never block a session start
        print(json.dumps({"systemMessage": f"Repo watch failed: {e}"}) if "--text" not in sys.argv else e)
