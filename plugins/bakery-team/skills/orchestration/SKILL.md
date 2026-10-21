---
name: orchestration
description: Rickroll Rick's (the main session's) part of the Cookie Empire workflow - feature branches, the phases of a feature, merging agent branches, the fix loop, opening the pull request, and how file ownership is enforced. Load it before running or merging a feature; the feature skill loads it. Agents don't need it.
---

# Orchestration (Rick only)

Read together with the `bakery-context` skill (team, ownership, gates, report format, token budget).

## Feature workflow (branches + pull requests)

Run a feature with **`/bakery-team:feature <name> <description>`** (`.claude/skills/feature/SKILL.md`); details and start gates are in the workflow (`bakery-context` skill).

1. **Branch:** Rickroll Rick (the main session) runs `git switch main && git pull && git switch -c feature/<name>` and stays on it, in the main checkout. He **never `cd`s into an agent worktree** (that moves the whole session); he uses `git -C <path>` and `mise -C <path> run …` / `--cd` instead.
2. **Brief:** drafts `docs/briefs/<name>.md` from the template, waits for the user's approval, commits it on the feature branch.
3. **Agents:** researcher first if needed; then model-designer, sound-designer, vfx-designer, balance-designer and coder in parallel (the coder uses new effect IDs and sound events from the brief while the designers add them; it waits only for a Java API that isn't on `main` yet, like the first `Effects` service), each in its own worktree **branched from the feature branch** (`.claude/settings.json`: `"worktree": { "baseRef": "head" }`), on branch `<name>/<agent>`, committing with its own identity. Agents never push, merge or touch `main`.
4. **Review + merge:** Gandalf reviews each code branch (asset-only branches skip the branch review, see "Token budget"); Rick runs `mise run ownership-check <name>/<agent>` (a violation goes back to the agent), merges `READY` branches into the feature branch with `git merge --no-ff` (assets and config before code), runs `check`, `validate-assets`, `sound-check` and `balance-check` after each merge, sends red checks back to the owner, resolves conflicts only where the owner is clear, then removes the merged worktree and branch (`git branch -d <name>/<agent>`, `git worktree prune`). Leftover `<name>/*` branches or worktrees are listed in the final summary.
5. **Pull request:** after Gandalf's integration review, Rick checks `gh auth status`, pushes `feature/<name>` (only `feature/*`, never force), and opens a PR **as `cookie-bakery[bot]`** with `mise run pr-open` (so the user can approve it; `main` requires 1 approval and the `check` job), filled from `.github/pull_request_template.md`: ready when everything is green and `READY`, otherwise draft with the open issues. The body includes a **Token usage** section: the output of `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/token_usage.py" report --feature <name>` (per agent), plus one line on where most tokens went. He waits for CI with `gh pr checks --watch`, fixes failures through the owners, **opens the PR in the user's browser automatically** (`gh pr view --web`) once the feature is fully implemented, and gives the user the URL and a 3-line summary.
6. **Merge:** the user reviews and merges the PR. Rick never merges into `main`.

## Branches at a glance

```
main ──────────────────────────────────────────────────────────── (user merges the PR)
  └─ feature/<name>            Rickroll Rick: brief, research notes, merges, integration review
       ├─ <name>/model-designer      agent worktree, branched from feature/<name>
       ├─ <name>/sound-designer      …
       ├─ <name>/vfx-designer
       ├─ <name>/balance-designer
       └─ <name>/plugin-coder
```

- **One branch per feature:** `feature/<name>`, created from an up-to-date `main`.
- **Agent branches** are named `<name>/<agent>` (not `feature/<name>/<agent>`: git can't have both `feature/<name>` and refs under it). Agents create them by renaming their worktree's branch (`git branch -m <name>/<agent>`).
- `.claude/settings.json` sets `"worktree": { "baseRef": "head" }`, so agent worktrees branch from the orchestrator's current `HEAD` (the feature branch) instead of `main`. The coder and designers have `isolation: worktree` in their frontmatter, so they always get one.
- Agents **never push, never touch `main`, never merge.** The orchestrator merges each agent branch into the feature branch after the tester approves it. The user reviews and merges the pull request into `main`.

## Phases of a feature

```
0. Branch         git switch main && git pull && git switch -c feature/<name>
1. Brief          /bakery-team:feature drafts docs/briefs/<name>.md; user approves; committed on the feature branch   (planned)
2. Research       researcher → docs/research/<topic>.md, committed on the feature branch                   (in progress)
3. Build          in parallel, each in its own worktree from the feature branch:
                    model-designer · sound-designer · vfx-designer · balance-designer · plugin-coder
4. Review         plugin-tester per code branch → READY / NOT READY (fix loop only for HIGH/MEDIUM); asset-only branches: checks only
5. Merge          READY agent branch → feature branch (merge --no-ff), one at a time, checks after each
5b. Cleanup      code owner does a behaviour-preserving simplify/efficiency pass (incl. Gandalf's PERF findings), reviewed like any branch; skipped if nothing to do
6. Integration    plugin-tester reviews the whole feature on the feature branch (incl. performance checks)
7. Pull request   push feature/<name>, open the PR (ready or draft), wait for CI                         (review)
8. Done           all green + READY → status done, PR marked ready; the user merges it; Rick cleans up   (done)
```

### Merging agent branches (orchestrator)
For each `READY` branch, one at a time:
1. `mise run ownership-check <name>/<agent>`. A violation goes back to the agent (fix on its branch, re-review); don't merge around it. Add `--human-approved` only when the user explicitly approved changes to human-controlled files on that branch; they're then listed for "Needs human review" instead of failing.
2. Merge as Rickroll Rick: `git -c user.name="Rickroll Rick" -c user.email="rick@bakery.invalid" merge --no-ff <name>/<agent>`
3. Run the checks (below), then clean up: `git worktree remove <path>` (unlock first if needed), `git branch -d <name>/<agent>`, `git worktree prune`.

Order, so assets and config land before the code that uses them:
1. research notes (committed directly on the feature branch as they land)
2. model-designer, then sound-designer (assets + `sounds.yml`)
3. vfx-designer (engine + `effects.yml`)
4. balance-designer (`buildings.yml`, `upgrades.yml`, model, golden values)
5. plugin-coder

After every merge, run `mise run check`, `mise run validate-assets`, `mise run sound-check` and `mise run balance-check`. A red check stops the line: send it to the owning agent, fix on its branch, re-review, merge again.

**Conflicts:** resolve only when every conflicting file has a clear owner and the right result is obvious (e.g. two appended sections). Otherwise abort the merge and ask the owning agent to rebase its change on the current feature branch, or ask the user.

**Leftovers:** at the end of a feature, `git branch --list '<name>/*'` and `git worktree list` must show nothing of this feature; list anything left in the final summary and the PR.

### Fix loop
`NOT READY` (only for HIGH/MEDIUM bugs or PERF-HIGH) goes back to the branch owner, in the same worktree and branch, with the tester's findings. LOW findings don't start a fix round; they go to the PR's follow-ups. When the owner reports `DONE` again, the tester re-reviews only what changed. Max 3 rounds; after that the orchestrator asks the user.

### Pull request
1. `gh auth status`: if not logged in, tell the user to run `gh auth login` and stop.
2. Push only the feature branch: `git push -u origin feature/<name>`. Never push `main`, never force-push.
3. Fill in `.github/pull_request_template.md` (summary, brief + acceptance criteria, team contributions from `git log main..HEAD --format="%an: %s"`, checks, tester verdict, needs human review, how to test in-game, follow-ups) into a body file, then:
   `mise run pr-open --head feature/<name> --base main --title "<title>" --body-file <file>`
   This opens the PR as the `cookie-bakery[bot]` GitHub App (token from `mise run pr-token`; config in `~/.config/cookieclicker/github-app.env`), so the user can approve it: `main`'s ruleset needs 1 approval and authors can't approve their own PRs. Rick runs it under the user's allow rule `Bash(mise run pr-open:*)`. If it fails or is denied, stop and give the user the exact `! mise run pr-open …` command; never fall back to `gh pr create` with the user's account.
   - **Ready** PR only when every check passes and the integration verdict is `READY`.
   - Otherwise add `--draft` and list the open issues in the body.
4. If `.github/workflows/` has a CI workflow: `gh pr checks --watch`. If CI fails, fix it through the owning agent, merge into the feature branch, push again (the PR updates), and re-check.
5. Give the user the PR URL, a 3-line summary, and any leftover `<name>/*` branches or worktrees. **The user reviews and merges the PR.** The orchestrator never merges it.

---

## Ownership enforcement

`.claude/ownership.json` maps every agent (`agent_type`) to its git identity and the path globs it may change (`**` any depth, `*` one segment, `!` excludes). Two layers use it:

| Layer | What | Covers | Guarantee |
|---|---|---|---|
| PreToolUse hook (`.claude/hooks/ownership.py`) | denies an `Edit`/`Write`/`NotebookEdit` outside the agent's globs, naming the owner | edits made with those tools, at write time | early warning only: **files written via Bash aren't covered** |
| `mise run ownership-check <branch>` | checks every non-merge commit on the branch against its **author's** globs | everything committed, however it was written | the real gate: Rick runs it before every merge |

- The hook reads the map and matcher only from the main checkout (`$CLAUDE_PROJECT_DIR`), so an agent can't loosen its rules from its worktree. Worktree paths are converted to repo-relative paths; paths outside the repo are allowed.
- Unknown agent types are denied inside the repo; read-only agents (`Explore`, `Plan`) never trigger it.
- **Human-controlled files** (`.claude/agents/`, `.claude/skills/`, the workflow (`bakery-context` skill), `.claude/ownership.*`, `.claude/hooks/`, `.claude/settings.json`): no agent may edit them. Rick gets an `ask` prompt and edits them only when the user explicitly asks; every change goes under "Needs human review" in the PR. Rick may otherwise edit only `CLAUDE.md`, `docs/briefs/` and `.github/`.
- Authorship is self-declared (`git -c user.name/email`), so the merge check guards against mistakes, not tampering. Merge commits are skipped for the author check; files changed while resolving conflicts are listed and go into the PR.
- Symlinks: the hook resolves paths with `realpath`, so a symlink inside the repo that points outside it counts as outside the repo and is allowed. Accepted, for the same reason: the hook catches mistakes, not deliberate workarounds; the merge check still sees what gets committed.
- **Rick never `cd`s into a worktree.** Changing directory into an agent's worktree moves the whole session there (isolation then blocks edits to the main checkout, and new agent worktrees would branch from the wrong `HEAD`). For anything inside an agent worktree he uses `git -C <path> …` and `mise -C <path> run …` (or `--cd`), and stays in the main checkout on the feature branch.

---
