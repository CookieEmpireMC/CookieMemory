---
name: bakery-context
description: Shared rules of the Cookie Empire team — who the agents are, their git identities, file ownership, the feature workflow (briefs, gates, merge order, fix loop, report format), and the ground rules. Preloaded by every bakery-team agent; read it before planning or running any feature.
---

# Cookie Empire team context

Shared by every repo in `CookieEmpireMC` that enables the `bakery-team` plugin. Repo-specific facts (what the repo is, its commands, its docs, its ownership map) are in that repo's `CLAUDE.md` and `.claude/ownership.json`; when they differ from this file, the repo wins for that repo.

## Working style (user rule)
Be decisive: one solid attempt, one check/review pass, fix only real failures, then commit and report. No repeated redesign or re-planning loops.

## Memory
Every repo keeps its own development memory: `.claude/agent-memory/bakery-team-<agent>/` per agent (plugin agents run as `bakery-team:<agent>`; Claude Code turns the ':' into '-' for the folder), `docs/briefs/`, `docs/reviews/`, `docs/architecture.md`. Write what is specific to the repo there. Shared knowledge (this file, the `game-design` skill, the agents) changes only through a pull request on `CookieEmpireMC/CookieMemory` that the user merges.

## Agents (plugin `bakery-team`)

| Agent | Role | Writes to |
|---|---|---|
| `resource-pack-researcher` | researches resource pack techniques for the target version | `docs/research/` only |
| `model-designer` | creates assets: models, item model definitions, .bbmodel, ItemsAdder YAML, placeholder textures, fonts/glyphs, pack.mcmeta, house design files | `resourcepack/` (see ownership), `itemsadder/`, `modelengine/`, `src/main/resources/houses/`, `design/` (its files) |
| `sound-designer` | creates original .ogg sounds (synthesized or processed CC0), sounds.json, subtitles, sounds.yml | `resourcepack/assets/<ns>/{sounds,sounds.json,lang}`, `src/main/resources/sounds.yml`, `design/sound-*`, `design/sounds.md`, `design/CREDITS.md` |
| `vfx-designer` | builds the effects engine (particles, display-entity effects) and its presets | `src/main/java/…/vfx/` + its tests, `src/main/resources/effects.yml`, particle files in the pack, `design/vfx-*`, `design/effects.md` |
| `balance-designer` | economy numbers, formula contract, pacing simulator and reports | `buildings.yml`, `upgrades.yml`, `tools/balance/`, `docs/balance/` |
| `plugin-coder` | implements features | `src/main/` except designer-owned files, `pom.xml`, `plugin.yml`, other config |
| `plugin-tester` | writes/runs tests, reviews architecture, gives a merge verdict | `src/test/`, `docs/reviews/`, `docs/architecture.md` |

### The team (git identities)

Everyone commits under their own name, per commit (`git -c user.name=… -c user.email=… commit`), never by changing git config. Each agent file's "Commits" section has its exact command and rules; `mise run team` shows commits per member.

| Agent | Name | Email | Motto |
|---|---|---|---|
| main session (orchestrator, merges into feature branches) | Rickroll Rick | rick@bakery.invalid | never gonna push to main, never gonna merge your PR |
| resource-pack-researcher | Citation Cindy | cindy@bakery.invalid | [citation needed] is a lifestyle |
| plugin-coder | Works4Me Wesly | wesly@bakery.invalid | it compiled on my machine |
| plugin-tester | Gandalf | gandalf@bakery.invalid | no branch passes without a verdict |
| model-designer | Pixel Pat | pat@bakery.invalid | no mistakes, just happy little texels |
| sound-designer | Bassboost Bruno | bruno@bakery.invalid | every click deserves a drop |
| vfx-designer | Flare Larry | larry@bakery.invalid | if it doesn't sparkle, it isn't done |
| balance-designer | Stonks Stan | stan@bakery.invalid | number go up (on schedule) |

The orchestrator commits as Rickroll Rick (`git -c user.name="Rickroll Rick" -c user.email="rick@bakery.invalid" …`), including research notes and integration reviews on behalf of agents without a shell or branch (credited with `--author`). Rick merges agent branches into the feature branch and opens the pull request; **only the user merges into `main`**.

### Asset ownership
- **model-designer:** models, item model definitions, textures, fonts/glyphs, `pack.mcmeta`, `itemsadder/`, `modelengine/`, house design files (`src/main/resources/houses/`)
- **sound-designer:** `.ogg` files, `sounds.json`, subtitle lang files, `sounds.yml`
- **vfx-designer:** the `vfx` package and its tests, `effects.yml`, particle definitions and textures
- **balance-designer:** `buildings.yml`, `upgrades.yml` (later golden cookie/prestige values), `tools/balance/`, `docs/balance/`
- **plugin-coder:** everything else in `src/main/` (incl. wiring the `Effects` service and the single sound service that reads `sounds.yml`), `pom.xml`, `plugin.yml`, other config; tooling (`tools/` except `tools/balance/` and tool tests, `mise.toml`, `.gitignore`, `.gitattributes`, `.mailmap`, `design/requirements.txt`) and the reference docs (`docs/paper-*.md`, `docs/toolchain.md`, `docs/minimessage.md`, `docs/integrations.md`). `mise.toml` and `.gitattributes` changes always go under "Needs human review" in the PR.
- **plugin-tester:** `src/test/`, tool tests (`tools/**/test_*.py`), `docs/reviews/`, `docs/architecture.md`
- **orchestrator (Rick):** `CLAUDE.md`, `docs/briefs/`, `.github/`, merge commits
- **Human-controlled (no agent):** `.claude/agents/`, `.claude/skills/`, the workflow (`bakery-context` skill), `.claude/ownership.*`, `.claude/hooks/`, `.claude/settings.json`. Rick edits them only when the user explicitly asks, and every change goes under "Needs human review".
- Nobody edits another owner's files; ask the owner instead.
- **Agent memory:** every agent has `memory: project`, a private cache in `.claude/agent-memory/bakery-team-<agent>/` (its `MEMORY.md` loads at startup) for verified facts it would otherwise rediscover each run. Only that agent may write it; what to store and what not is in the workflow (`bakery-context` skill) → "Agent memory".
- **Enforced** by `.claude/ownership.json` in two layers: a PreToolUse hook that denies `Edit`/`Write`/`NotebookEdit` outside an agent's globs (early warning; Bash-written files aren't covered), and `mise run ownership-check <branch>`, which checks every commit against its author's globs before Rick merges (the real gate; authorship is self-declared, so it catches mistakes, not tampering). Details in the workflow (`bakery-context` skill).

Every agent that writes code or assets runs in its own worktree (`isolation: worktree` in its frontmatter), branched from the feature branch, on branch `<name>/<agent>`. Agent branches are merged into the feature branch one at a time; the feature reaches `main` only through a pull request the user merges.

## Feature workflow (branches + pull requests)

Run a feature with **`/bakery-team:feature <name> <description>`** (`.claude/skills/feature/SKILL.md`); details and start gates are in the workflow (`bakery-context` skill).

1. **Branch:** Rickroll Rick (the main session) runs `git switch main && git pull && git switch -c feature/<name>` and stays on it, in the main checkout. He **never `cd`s into an agent worktree** (that moves the whole session); he uses `git -C <path>` and `mise -C <path> run …` / `--cd` instead.
2. **Brief:** drafts `docs/briefs/<name>.md` from the template, waits for the user's approval, commits it on the feature branch.
3. **Agents:** researcher first if needed; then model-designer, sound-designer, vfx-designer, balance-designer and coder in parallel (the coder uses new effect IDs and sound events from the brief while the designers add them; it waits only for a Java API that isn't on `main` yet, like the first `Effects` service), each in its own worktree **branched from the feature branch** (`.claude/settings.json`: `"worktree": { "baseRef": "head" }`), on branch `<name>/<agent>`, committing with its own identity. Agents never push, merge or touch `main`.
4. **Review + merge:** Gandalf reviews each agent branch; Rick runs `mise run ownership-check <name>/<agent>` (a violation goes back to the agent), merges `READY` branches into the feature branch with `git merge --no-ff` (assets and config before code), runs `check`, `validate-assets`, `sound-check` and `balance-check` after each merge, sends red checks back to the owner, resolves conflicts only where the owner is clear, then removes the merged worktree and branch (`git branch -d <name>/<agent>`, `git worktree prune`). Leftover `<name>/*` branches or worktrees are listed in the final summary.
5. **Pull request:** after Gandalf's integration review, Rick checks `gh auth status`, pushes `feature/<name>` (only `feature/*`, never force), and opens a PR **as `cookie-bakery[bot]`** with `mise run pr-open` (so the user can approve it; `main` requires 1 approval and the `check` job), filled from `.github/pull_request_template.md`: ready when everything is green and `READY`, otherwise draft with the open issues. He waits for CI with `gh pr checks --watch`, fixes failures through the owners, **opens the PR in the user's browser automatically** (`gh pr view --web`) once the feature is fully implemented, and gives the user the URL and a 3-line summary.
6. **Merge:** the user reviews and merges the PR. Rick never merges into `main`.

## Ground rules

- Detect the target version from `pom.xml` first, and follow only that version's reference.
- Java, Maven and Python are pinned in `mise.toml` (Java 21 for 1.21.x, Java 25 for 26.x). Build with `mise run build`, test with `mise run test`, full check with `mise run check`, check assets with `mise run validate-assets` and `mise run sound-check`, check pacing with `mise run balance-check`, zip the pack with `mise run pack`. Never run plain `mvn`; use `mise exec -- mvn …`. CI (`.github/workflows/ci.yml`) runs `check`, `validate-assets`, `sound-check` and `balance-check` on every push and PR, so run them locally before handing work back.
- Never shade Paper, Adventure/MiniMessage, ItemsAdder or ModelEngine; they use `provided` scope.
- Never hardcode sounds or particles in code: sounds go through `sounds.yml` events, effects through `Effects.play(id)`.
- Never set balance values in code: costs, CPS, multipliers and unlocks come only from `buildings.yml` / `upgrades.yml`, with the maths from `docs/balance/model.md`.
- If a feature needs something the target version or an integration doesn't support, stop and report it instead of working around it.


## Workflow: who runs when

Reference for all agents and the orchestrator. Agents can't see or wait for each other while running, so all coordination goes through **files on the feature branch** and **reports to the orchestrator**. Each agent checks its start conditions, does its job, and reports in a fixed format. The orchestrator launches the next agents.

---

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

## Roles

| Role | Who | Works in |
|---|---|---|
| **Orchestrator**: Rickroll Rick | the main Claude session talking to the user | the main checkout, on `feature/<name>` |
| resource-pack-researcher | agent | the main checkout, `docs/research/` only (no worktree, no shell; the orchestrator commits its notes) |
| model-designer, sound-designer, vfx-designer, balance-designer, plugin-coder | agents | their own worktree, branch `<name>/<agent>` |
| plugin-tester | agent | the worktree of the branch it reviews (only after that branch's owner has stopped), or the feature branch for an integration review |

Everyone commits under their own git identity; see "The team" in `CLAUDE.md` and the Commits section of each agent file.

---

## The feature brief: the contract everyone builds against

Every feature starts with a brief: `docs/briefs/<name>.md`, copied from `docs/briefs/TEMPLATE.md` (goal, player story, acceptance criteria, out of scope, assets needed, balance impact, research needed, open questions, contract, tasks, status, merge order, human review). The easiest way is the **`/bakery-team:feature <name> <description>`** skill, which runs this whole workflow.

The brief's **Status** line tracks the feature: `planned` (drafted, waiting for approval) → `in progress` (agents running) → `review` (pull request open, draft or waiting on CI) → `done` (green, `READY`, PR marked ready; set in the PR's last commit so merging lands it on `main`). The **Status** table inside tracks each agent.

- **Contract first.** Everyone uses exactly the IDs in the brief's Contract section. That's what lets designers and the coder work in parallel: the coder references `cookie_click` before the sound exists, and the sound-designer delivers exactly that name.
- Agents **never edit the brief**. If an ID is wrong or missing, propose the change under `CONTRACT CHANGES` in your report; the orchestrator updates the brief.
- Only the orchestrator updates the **Status** table, based on reports.

---

## Phases of a feature

```
0. Branch         git switch main && git pull && git switch -c feature/<name>
1. Brief          /bakery-team:feature drafts docs/briefs/<name>.md; user approves; committed on the feature branch   (planned)
2. Research       researcher → docs/research/<topic>.md, committed on the feature branch                   (in progress)
3. Build          in parallel, each in its own worktree from the feature branch:
                    model-designer · sound-designer · vfx-designer · balance-designer · plugin-coder
4. Review         plugin-tester per agent branch → READY / NOT READY (+ fix loop with the owner)
5. Merge          READY agent branch → feature branch (merge --no-ff), one at a time, checks after each
5b. Cleanup      code owner does a behaviour-preserving simplify/efficiency pass (incl. Gandalf's PERF findings), reviewed like any branch; skipped if nothing to do
6. Integration    plugin-tester reviews the whole feature on the feature branch (incl. performance checks)
7. Pull request   push feature/<name>, open the PR (ready or draft), wait for CI                         (review)
8. Done           all green + READY → status done, PR marked ready; the user merges it; Rick cleans up   (done)
```

### Start conditions (gates)

| Agent | Can start when | Does NOT wait for |
|---|---|---|
| researcher | the brief exists (or the orchestrator asks directly) | anyone |
| model-designer | brief contract lists its assets; research note on the feature branch if the brief says "Needs research: yes" | coder, other designers |
| sound-designer | same as model-designer, for sound events | coder, other designers |
| vfx-designer | same, for effect IDs; and any item model its effects use is in the contract | coder, other designers |
| balance-designer | the brief lists a balance impact (new buildings/upgrades/prices/rewards) | coder, other designers |
| plugin-coder | brief exists; research note on the feature branch if needed; every feature in "Depends on" is merged into `main`; and any **new** Java API from another owner it calls is already merged into the feature branch (see below) | designers' assets and final balance numbers (code against contract IDs and `docs/balance/model.md`; vanilla fallbacks cover missing assets) |
| plugin-tester (branch) | that branch's owner reported `DONE` and has stopped | other branches |
| plugin-tester (integration) | all agent branches of the feature are merged into the feature branch | — |

**Java code dependencies are the one hard wait.** Assets can arrive later because of IDs and fallbacks, but code can't compile against an API that isn't on the branch.
- **Once `Effects.play(id)` is on `main`** (the normal case): the coder starts **in parallel** with the designers. It calls `Effects.play("<new_id>", …)` and plays sound events by the names in the brief's contract, while the vfx-designer and sound-designer add the matching presets and sounds. Unknown IDs are logged and skipped at runtime, so the code works before the assets land.
- **Only while the `Effects` service doesn't exist on `main` yet** (the first effects feature), or when the coder needs a *new* API method from another owner: merge that branch into the feature branch first, then launch the coder (worktrees branch from the orchestrator's `HEAD`).

### If a gate isn't met
Stop and report `STATUS: BLOCKED` with exactly what you're waiting for. Don't invent IDs, stub another owner's code, or edit files you don't own to get unblocked.

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
`NOT READY` goes back to the branch owner, in the same worktree and branch, with the tester's findings. When the owner reports `DONE` again, the tester re-reviews only what changed. Max 3 rounds; after that the orchestrator asks the user.

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

## Agent memory (token cache)

Every agent has `memory: project` in its frontmatter: a persistent folder `.claude/agent-memory/bakery-team-<agent>/` that only that agent may write (ownership map). The first 200 lines / 25 KB of its `MEMORY.md` load automatically at startup, so it doesn't have to rediscover the same facts every run.

**Store** (one short line each in `MEMORY.md`, details in topic files it links to, with date + source):
- facts that were expensive to find: exact API signatures/constants verified in the Javadocs for this version, pack format numbers, enum names, working command lines
- gotchas and their fixes (tool quirks, things that failed and why)
- where things live in this repo (paths, entry points, which file defines what)
- decisions the user made that affect your work and aren't in a brief yet

**Don't store:** secrets or tokens; anything already in `CLAUDE.md`, `docs/`, the brief or the code (link to it instead); one-off task details; guesses (only verified facts).

**Keep it lean:** `MEMORY.md` is an index under 200 lines; update or delete entries that turn out wrong or stale; check a remembered fact against the current code or docs before relying on it for something risky.

**Lifecycle** (verified 2026-10-18): project memory lands in the checkout you run in.
- **Isolated agents** (`isolation: worktree`: coder and designers): memory is in your worktree's `.claude/agent-memory/bakery-team-<agent>/` (writing to the main checkout is blocked by worktree isolation). **Commit it yourself on your branch** like any other file; it reaches the feature branch with your merge and loads in your next worktree.
- **Agents without their own worktree** (researcher; tester working from the main checkout): memory lands in the main checkout. Rick commits it on the feature branch, credited to you (`--author="<your name> <your email>"`).
Either way it reaches `main` through the feature PR. The designers' `design/*style-guide.md` and `design/*lessons.md` stay the human-readable design record; memory is your private working cache.

---

## Rules for every agent

- **Read first:** the workflow (`bakery-context` skill) (this file) and the feature brief you were given (`docs/briefs/<name>.md`).
- **Own files only.** See "Asset ownership" in `CLAUDE.md`. Need something from another owner? Put it under `REQUESTS` in your report.
- **Git:** follow the Commits section of your agent file: your own identity per commit, only your own files, only on your own branch, small commits, checks first. Never push, merge, rebase, amend or force, and never touch `main` or the feature branch directly.
- **Don't wait in a loop.** If you're blocked, report and stop. The orchestrator re-launches you when the gate is met.

### Report format (end every run with this)

```
STATUS: DONE | BLOCKED | NEEDS-INPUT
FEATURE: <name>
BRANCH: <name>/<agent>, or "feature/<name> (docs only)"
PRODUCED: files, plus the IDs/names others will use
CONTRACT CHANGES: proposed changes to the brief's contract, or none
REQUESTS: <owner>: <what you need from them>, or none
WAITING FOR: (only if BLOCKED) the exact gate that isn't met
NEXT: who can start now because of this work
```

The tester also adds `VERDICT: READY | NOT READY` and, at integration, a `MERGE ORDER` line.

