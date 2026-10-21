---
name: repo-news
description: Show what was pushed to the Cookie Empire repos since you last looked (by you or a teammate), fetch it, and fast-forward local branches that are safely behind. Use when the user asks what's new or whether someone pushed. Keep it running in a session with `/loop 15m /bakery-team:repo-news`.
---

Launch the `bakery-team:repo-watcher` agent (Gossip Gus) with: "Check the Cookie Empire repos for news and report." Relay its report to the user as it is, in a few lines. If it says nothing is new, say so in one line.

A short version of the same report also appears automatically at the start of every session (the `SessionStart` hook `hooks/repo_watch.py`).
