# CookieMemory

The shared brain of the **Cookie Empire** team (`CookieEmpireMC`). It is a Claude Code plugin marketplace (`cookie-memory`) with one plugin, **`bakery-team`**, which every repo in the organisation enables.

| Path | What |
|---|---|
| `plugins/bakery-team/agents/` | the 8 agents (`bakery-team:plugin-coder`, `bakery-team:plugin-tester`, `bakery-team:model-designer`, `bakery-team:sound-designer`, `bakery-team:vfx-designer`, `bakery-team:balance-designer`, `bakery-team:resource-pack-researcher`, `bakery-team:repo-watcher`) |
| `plugins/bakery-team/skills/feature/` | `/bakery-team:feature <name> <description>`: one feature end to end |
| `plugins/bakery-team/skills/bakery-context/` | team, git identities, ownership, gates, report format, token budget, ground rules (preloaded by every agent) |
| `plugins/bakery-team/skills/orchestration/` | Rick's part: branches, phases, merging, fix loop, PR, ownership enforcement (loaded by the `feature` skill, not by agents) |
| `plugins/bakery-team/skills/game-design/` | the game design document: a short summary (preloaded by every agent) and the full text in `gdd.md` (read per section when needed) |
| `plugins/bakery-team/skills/token-report/` | `/bakery-team:token-report`: tokens per agent, feature or run |
| `plugins/bakery-team/scripts/token_usage.py` | records and reports token usage (also run by the SubagentStop/SessionEnd hook) |
| `plugins/bakery-team/skills/repo-news/` | `/bakery-team:repo-news`: what was pushed to the Cookie Empire repos since you last looked |
| `plugins/bakery-team/hooks/` | the ownership hook (denies edits outside an agent's paths, reading the **repo's** `.claude/ownership.json`) and the repo watch (`repo_watch.py`, below) |
| `tools/check_plugin.py` | the CI check |

## What stays in each repo
Each repo keeps what is specific to it: `CLAUDE.md`, `.claude/ownership.json`, `.claude/settings.json` (with `worktree.baseRef: head`), `docs/briefs/`, `docs/reviews/`, `docs/architecture.md`, and the agents' memory in `.claude/agent-memory/bakery-team-<agent>/`.

## Use it in a repo
Add to the repo's `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "cookie-memory": { "source": { "source": "github", "repo": "CookieEmpireMC/CookieMemory" }, "autoUpdate": true }
  },
  "enabledPlugins": { "bakery-team@cookie-memory": true }
}
```
Then open the repo in Claude Code and trust the folder. The repo is private, so git must be able to reach GitHub: an SSH key, or `gh auth login && gh auth setup-git` (then set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`). If the plugin doesn't show up, run `/plugin install bakery-team@cookie-memory`.

## Change the team or the game design
The full game design is `plugins/bakery-team/skills/game-design/gdd.md`; when you change it, update the summary in that skill's `SKILL.md` too.

1. Branch, edit, run `python tools/check_plugin.py`, open a PR. The user reviews and merges.
2. There is no `version` field, so every merged commit is a new version. With `autoUpdate` it arrives on the next session; otherwise run `/plugin marketplace update cookie-memory`, then `/reload-plugins`.
3. Test before merging: `claude --plugin-dir ./plugins/bakery-team` in a repo.

## Repo watch: stay up to date with each other's pushes
Every time a Claude Code session starts in a Cookie Empire repo, the `SessionStart` hook `hooks/repo_watch.py`:
1. finds every git repo **next to** the current one whose origin is `github.com/CookieEmpireMC` (keep all the repos in one folder, or set `COOKIE_EMPIRE_DIR`), and runs `git fetch --prune` on each one;
2. shows you which commits anyone pushed since you last looked, per repo and branch (what you've already seen is stored per machine in `~/.local/state/cookie-empire/repo-watch.json`), and tells Claude as well;
3. fast-forwards local branches that are only behind their `origin` branch. A branch with its own commits, or one checked out with uncommitted changes, is never touched, only reported;
4. when CookieMemory `main` changed, reminds you that the team and the game design update on the next session (`autoUpdate`), or now with `/plugin marketplace update cookie-memory` and then `/reload-plugins`.

The first run only records what's there. During a long session, run `/bakery-team:repo-news` (Gossip Gus, the `repo-watcher` agent, explains what changed and whether it affects your work), or keep it going with `/loop 15m /bakery-team:repo-news`. By hand: `python3 plugins/bakery-team/hooks/repo_watch.py --text` (`--peek` doesn't mark anything as seen or pull).

## Token usage: where do the tokens go?
Claude Code keeps a transcript of every session and subagent. When an agent finishes (`SubagentStop`) or a session ends (`SessionEnd`), `scripts/token_usage.py --hook` adds that session's runs to a ledger on your machine (`~/.local/state/cookie-empire/token-usage.json`), so the numbers survive Claude Code's transcript cleanup.

- `/bakery-team:token-report`, or by hand:
  - `python3 plugins/bakery-team/scripts/token_usage.py report --by agent|feature|run [--feature NAME] [--repo NAME] [--since YYYY-MM-DD]`
- Every feature PR gets a **Token usage** table (per agent), so you and your friend can compare features on GitHub.
- **Columns:**
  - API calls and tool uses.
  - Input (uncached), cache write, cache read, output.
  - **Weighted**: the input-token equivalent with the API's relative prices (cache write 1.25×, cache read 0.1×, output 5×). Use it to rank costs within one model; across models, also look at the model column.
- **Grouping:**
  - Each subagent run is counted under the feature from its prompt ("Feature `x`") or its branch.
  - The main session (Rick) is split by the `feature/*` branch it was on.
  - Usage on other branches shows as feature `-`.

The ledger is per machine; your friend's runs are in theirs.

## Token budget rules
The workflow (`bakery-context` → "Token budget") keeps tests and reviews lean:
- Only important code is tested.
- Asset-only branches skip Gandalf's branch review.
- LOW findings go to follow-ups instead of a fix round.
