---
name: bakery-context
description: Shared rules of the Cookie Empire team — who the agents are, their git identities, file ownership, the feature workflow (briefs, gates, merge order, fix loop, report format), and the ground rules. Preloaded by every bakery-team agent; read it before planning or running any feature.
---

# Cookie Empire team context

Shared by every repo in `CookieEmpireMC` that enables the `bakery-team` plugin. Repo-specific facts (what the repo is, its commands, its docs, its ownership map) are in that repo's `CLAUDE.md` and `.claude/ownership.json`; when they differ from this file, the repo wins for that repo.

## Working style (user rule)
Be decisive: one solid attempt, one check/review pass, fix only real failures, then commit and report. No repeated redesign or re-planning loops.

## Token budget (user rule)
Spend tokens where they catch real problems:
- **Lean tests:** only the important code (economy maths, data that could be lost, player/world safety, shipped-file loading, contracts, regressions for real bugs). No coverage target and no test per class; the suite stays small (CookieClicker 2026-10-23: 686 tests trimmed to ~390 by value). Details are in the plugin-tester agent.
- **Lean reviews:** Gandalf reviews **code** branches: plugin-coder, and designer branches that change Java or Python tools. Rick merges **asset-only** branches (models, textures, sounds, effect presets, balance numbers) after `ownership-check` and the asset checks, without a branch review; Gandalf sees them once in the integration review.
- **No fix round for LOWs:** only HIGH/MEDIUM bugs and PERF-HIGH go back to the owner. LOW findings become PR follow-ups.
- **Small jobs, small teams:** a change with one owner and a few files is one agent run plus checks, without designers or a branch review. Follow-ups for an agent that already worked on the feature go back to it (resumed, context still cached) instead of a new launch.
- **Quiet checks:** during your work run `mise run check-quiet` when the repo has it (it prints only the result and failures), not `mise run check`, and pipe other long outputs through `tail`/`grep`. Every line you read stays in your context and is paid for on every later call.
- **Batch independent steps:** every time you stop to look at a tool result, the whole context is read again. When the next reads, searches or commands don't depend on each other's results (reading 3 files, running 2 checks), issue them together in one step. Only wait for a result when the next step needs it.
- **Read narrowly:** open the files and sections you need (with `offset`/`limit` or `grep -n`), not whole directories or files; reuse your memory instead of rediscovering.
- **Split big code work:** a big feature gets 2–3 plugin-coder runs in parallel on separate parts instead of one long run (a run's cost grows faster than its length, because every call re-reads everything before it). See "Parallel coders" in the `orchestration` skill.
- **Quality first:** these rules cut repeated reading, not thinking. When a task needs the full GDD section, a reference doc, the Javadocs or a closer look at code, read it.
- **Measure:** every run's tokens are recorded per machine (SubagentStop/SessionEnd hook). `/bakery-team:token-report` shows them per agent, feature or run, and every feature PR gets a "Token usage" table.

## Code standards (user rule, 2026-10-23)
Each repo's `docs/architecture.md` has a **Standards** section (plugin-tester keeps it); the short version:
- **Comments:** only what the code can't say: a non-obvious *why* (version quirks, client behaviour, thread rules, maths), public API contracts the name doesn't cover, and format notes in files admins edit. No comments that repeat the code, narrate history ("since 1.1.0", "was …", brief/feature names) or explain the obvious. Javadoc 1–2 lines, only where needed, and **no `@param`/`@return` tags** (plugins publish no Javadoc): put units, ranges and special values (ticks, blocks/second, `0 = off`, what `null` means) in one doc line or in the parameter name.
- **Structure:** package by feature (sub-packages once a package passes ~25 classes), one responsibility per class, classes under ~500 lines, methods under ~60; shared helpers instead of copies (e.g. a `WarnOnce` logger, backup/file helpers). No wildcard imports, no package cycles (`config` imports no feature package).
- **Types:** records and `final` fields by default; `@Nullable` or `Optional` on purpose, never silent `null` returns.

## Config (user rule, 2026-10-23)
`config.yml` holds only what an admin really sets: resource pack (**first section**), database, feature on/off switches, server-load distances, debug. Internal tuning (render offsets, scales, tick timings, geometry, colours, fallback materials/blocks) are constants in code with the same values; every kept key has a built-in default, so an old or partial config loads cleanly. Balance values stay in `buildings.yml` / `upgrades.yml`, sounds in `sounds.yml`, effects in `effects.yml`.

## Performance (user rule, 2026-10-23)
- **Hot paths** (per tick, per click, per second per player, per block move): no repeated parsing (pre-compile MiniMessage templates once, e.g. a marker template that swaps values and is tested to equal a real parse), no allocations or region queries that an early-out can skip (bounding box per world before a WorldGuard lookup).
- **Scheduled tasks:** each has a reason; repeating tasks start on demand and stop themselves when idle (no riders, no views, no loops); one shared task instead of one per player; never two tasks doing the same recompute.
- **Saving:** batched in one transaction off the main thread; skip players/rows unchanged since the last save, but quit and shutdown always write.
- **Async:** only after a **spark** profile shows a call matters, and only for work the repo's research note marks safe (pure maths, serialization, JDBC). Entities, world, scoreboard/visibility and WorldGuard queries stay on the main thread.
- Big clean-ups measure before/after with a small timing test (no JMH) and record it in `docs/reviews/`.

## Plugin descriptor (Paper 26.x)
Use **`paper-plugin.yml`** (no `plugin.yml`; Paper prefers it when both exist). Libraries (JDBC drivers, pools) load through a `PluginLoader` + `MavenLibraryResolver` on `MavenLibraryResolver.MAVEN_CENTRAL_DEFAULT_MIRROR`, never Maven Central directly; versions come from a pom-filtered properties file plus a test that ties them to the pom. Plugins we call (WorldGuard) go under `dependencies.server` with `load: BEFORE`, `required`, `join-classpath: true`. Commands via Brigadier `LifecycleEvents.COMMANDS`; permissions declared in the descriptor (test the string matches the code). Paper plugins are still marked experimental: re-test a first start on every Paper bump.

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
| `plugin-coder` | implements features | `src/main/` except designer-owned files, `pom.xml`, `paper-plugin.yml`, other config |
| `plugin-tester` | writes/runs tests, reviews architecture, gives a merge verdict | `src/test/`, `docs/reviews/`, `docs/architecture.md` |
| `repo-watcher` | fetches every Cookie Empire repo, fast-forwards local branches that are safely behind, reports what was pushed (also runs at session start as a hook) | nothing (read-only apart from git fetch/fast-forward) |

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
| repo-watcher | Gossip Gus | gus@bakery.invalid | did you hear what got pushed? |

The orchestrator commits as Rickroll Rick (`git -c user.name="Rickroll Rick" -c user.email="rick@bakery.invalid" …`), including research notes and integration reviews on behalf of agents without a shell or branch (credited with `--author`). Rick merges agent branches into the feature branch and opens the pull request; **only the user merges into `main`**.

### Asset ownership
- **model-designer:** models, item model definitions, textures, fonts/glyphs, `pack.mcmeta`, `itemsadder/`, `modelengine/`, house design files (`src/main/resources/houses/`)
- **sound-designer:** `.ogg` files, `sounds.json`, subtitle lang files, `sounds.yml`
- **vfx-designer:** the `vfx` package and its tests, `effects.yml`, particle definitions and textures
- **balance-designer:** `buildings.yml`, `upgrades.yml` (later golden cookie/prestige values), `tools/balance/`, `docs/balance/`
- **plugin-coder:** everything else in `src/main/` (incl. wiring the `Effects` service and the single sound service that reads `sounds.yml`), `pom.xml`, `paper-plugin.yml`, other config; tooling (`tools/` except `tools/balance/` and tool tests, `mise.toml`, `.gitignore`, `.gitattributes`, `.mailmap`, `design/requirements.txt`) and the reference docs (`docs/paper-*.md`, `docs/toolchain.md`, `docs/minimessage.md`, `docs/integrations.md`). `mise.toml` and `.gitattributes` changes always go under "Needs human review" in the PR.
- **plugin-tester:** `src/test/`, tool tests (`tools/**/test_*.py`), `docs/reviews/`, `docs/architecture.md`
- **orchestrator (Rick):** `CLAUDE.md`, `docs/briefs/`, `.github/`, merge commits
- **Human-controlled (no agent):** `.claude/agents/`, `.claude/skills/`, the workflow (`bakery-context` skill), `.claude/ownership.*`, `.claude/hooks/`, `.claude/settings.json`. Rick edits them only when the user explicitly asks, and every change goes under "Needs human review".
- Nobody edits another owner's files; ask the owner instead.
- **Agent memory:** every agent has `memory: project`, a private cache in `.claude/agent-memory/bakery-team-<agent>/` (its `MEMORY.md` loads at startup) for verified facts it would otherwise rediscover each run. Only that agent may write it; what to store and what not is in the workflow (`bakery-context` skill) → "Agent memory".
- **Enforced** by `.claude/ownership.json` in two layers: a PreToolUse hook that denies `Edit`/`Write`/`NotebookEdit` outside an agent's globs (early warning; Bash-written files aren't covered), and `mise run ownership-check <branch>`, which checks every commit against its author's globs before Rick merges (the real gate; authorship is self-declared, so it catches mistakes, not tampering). Details in the workflow (`bakery-context` skill).

Every agent that writes code or assets runs in its own worktree (`isolation: worktree` in its frontmatter), branched from the feature branch, on branch `<name>/<agent>`. Agent branches are merged into the feature branch one at a time; the feature reaches `main` only through a pull request the user merges.

## Orchestrator-only details
Branches, the phases of a feature, merging, the fix loop, the pull request and how ownership is enforced are in the **`orchestration`** skill. Rick loads it (the `feature` skill does it for him); agents don't need it. Agents follow the gates, report format and rules below.

## Ground rules

- The target is **Paper 26.x** (Java 25), with the exact minor version (26.1, 26.2, 26.3, …) from the `paper-api` version in `pom.xml`. Follow `docs/paper-26x-reference.md`, and use only API, pack formats and features that exist in that minor version. If `pom.xml` isn't on 26.x, stop and report it.
- Java, Maven and Python are pinned in `mise.toml` (Java 25). Build with `mise run build`, test with `mise run test`, full check with `mise run check`, check assets with `mise run validate-assets` and `mise run sound-check`, check pacing with `mise run balance-check`, zip the pack with `mise run pack`. Never run plain `mvn`; use `mise exec -- mvn …`. CI (`.github/workflows/ci.yml`) runs `check`, `validate-assets`, `sound-check` and `balance-check` on every push and PR, so run them locally before handing work back.
- Never shade Paper, Adventure/MiniMessage, ItemsAdder or ModelEngine; they use `provided` scope.
- Never hardcode sounds or particles in code: sounds go through `sounds.yml` events, effects through `Effects.play(id)`.
- Never set balance values in code: costs, CPS, multipliers and unlocks come only from `buildings.yml` / `upgrades.yml`, with the maths from `docs/balance/model.md`.
- If a feature needs something the target version or an integration doesn't support, stop and report it instead of working around it.


## Workflow: who runs when

Reference for all agents and the orchestrator. Agents can't see or wait for each other while running, so all coordination goes through **files on the feature branch** and **reports to the orchestrator**. Each agent checks its start conditions, does its job, and reports in a fixed format. The orchestrator launches the next agents.

---

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

### Start conditions (gates)

| Agent | Can start when | Does NOT wait for |
|---|---|---|
| researcher | the brief exists (or the orchestrator asks directly) | anyone |
| model-designer | brief contract lists its assets; research note on the feature branch if the brief says "Needs research: yes" | coder, other designers |
| sound-designer | same as model-designer, for sound events | coder, other designers |
| vfx-designer | same, for effect IDs; and any item model its effects use is in the contract | coder, other designers |
| balance-designer | the brief lists a balance impact (new buildings/upgrades/prices/rewards) | coder, other designers |
| plugin-coder | brief exists; research note on the feature branch if needed; every feature in "Depends on" is merged into `main`; and any **new** Java API from another owner it calls is already merged into the feature branch (see below) | designers' assets and final balance numbers (code against contract IDs and `docs/balance/model.md`; vanilla fallbacks cover missing assets) |
| plugin-tester (branch) | a **code** branch's owner reported `DONE` and has stopped (asset-only branches get no branch review) | other branches |
| plugin-tester (integration) | all agent branches of the feature are merged into the feature branch | — |

**Java code dependencies are the one hard wait.** Assets can arrive later because of IDs and fallbacks, but code can't compile against an API that isn't on the branch.
- **Once `Effects.play(id)` is on `main`** (the normal case): the coder starts **in parallel** with the designers. It calls `Effects.play("<new_id>", …)` and plays sound events by the names in the brief's contract, while the vfx-designer and sound-designer add the matching presets and sounds. Unknown IDs are logged and skipped at runtime, so the code works before the assets land.
- **Only while the `Effects` service doesn't exist on `main` yet** (the first effects feature), or when the coder needs a *new* API method from another owner: merge that branch into the feature branch first, then launch the coder (worktrees branch from the orchestrator's `HEAD`).

### If a gate isn't met
Stop and report `STATUS: BLOCKED` with exactly what you're waiting for. Don't invent IDs, stub another owner's code, or edit files you don't own to get unblocked.

## Agent memory (token cache)

Every agent has `memory: project` in its frontmatter: a persistent folder `.claude/agent-memory/bakery-team-<agent>/` that only that agent may write (ownership map). The first 200 lines / 25 KB of its `MEMORY.md` load automatically at startup, so it doesn't have to rediscover the same facts every run.

**Store** (one short line each in `MEMORY.md`, details in topic files it links to, with date + source):
- facts that were expensive to find: exact API signatures/constants verified in the Javadocs for this version, pack format numbers, enum names, working command lines
- gotchas and their fixes (tool quirks, things that failed and why)
- where things live in this repo (paths, entry points, which file defines what)
- decisions the user made that affect your work and aren't in a brief yet

**Don't store:** secrets or tokens; anything already in `CLAUDE.md`, `docs/`, the brief or the code (link to it instead); one-off task details; guesses (only verified facts).

**Keep it lean and current:** `MEMORY.md` is an index under 200 lines; update or delete entries that turn out wrong or stale; check a remembered fact against the current code or docs before relying on it for something risky. When a better way replaces an old one, or classes move, **delete the old fact** in the same run instead of adding a second one. Prefer a few topic files (API facts, tooling, repo rules) over one file per feature; a per-feature note whose lesson is now in the code or docs gets deleted.

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
