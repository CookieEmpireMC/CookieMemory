# CookieMemory

The shared brain of the **Cookie Empire** team (`CookieEmpireMC`). It is a Claude Code plugin marketplace (`cookie-memory`) with one plugin, **`bakery-team`**, which every repo in the organisation enables.

| Path | What |
|---|---|
| `plugins/bakery-team/agents/` | the 7 agents (`bakery-team:plugin-coder`, `bakery-team:plugin-tester`, `bakery-team:model-designer`, `bakery-team:sound-designer`, `bakery-team:vfx-designer`, `bakery-team:balance-designer`, `bakery-team:resource-pack-researcher`) |
| `plugins/bakery-team/skills/feature/` | `/bakery-team:feature <name> <description>`: one feature end to end |
| `plugins/bakery-team/skills/bakery-context/` | team, git identities, ownership, workflow, ground rules (preloaded by every agent) |
| `plugins/bakery-team/skills/game-design/` | the game design document (preloaded by every agent) |
| `plugins/bakery-team/hooks/` | the ownership hook: denies edits outside an agent's paths, reading the **repo's** `.claude/ownership.json` |
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
1. Branch, edit, run `python tools/check_plugin.py`, open a PR. The user reviews and merges.
2. There is no `version` field, so every merged commit is a new version. With `autoUpdate` it arrives on the next session; otherwise run `/plugin marketplace update cookie-memory`, then `/reload-plugins`.
3. Test before merging: `claude --plugin-dir ./plugins/bakery-team` in a repo.
