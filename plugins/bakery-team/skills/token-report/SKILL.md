---
name: token-report
description: Show how many tokens the Cookie Empire agents used, per agent, per feature or per run, with cache hit rate and a cost-weighted total, to find where to save tokens. Use when the user asks about token usage, cost, or which agent/feature is expensive.
---

Run, choosing the grouping and filters from the user's question:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py" report --by agent|feature|run [--feature NAME] [--repo NAME] [--since YYYY-MM-DD]
```

(Default `--by agent` over everything. If `CLAUDE_PLUGIN_ROOT` is empty: `ls ~/.claude/plugins/cache/cookie-memory/bakery-team/*/scripts/token_usage.py | tail -1`.)

Show the table, then 2–4 short insights from it:
- which agents or features cost the most (use the **Weighted** column, and remember opus costs more per token than sonnet or haiku);
- runs with a low cache hit rate or many tool uses for what they did;
- one concrete suggestion to save tokens, e.g. a cheaper model for an agent, a shorter brief, fewer re-reviews, or less exploration.
