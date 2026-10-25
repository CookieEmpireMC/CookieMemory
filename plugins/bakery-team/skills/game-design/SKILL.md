---
name: game-design
description: The user's game design document for the Cookie Empire Minecraft server - a short summary of every section (concept, plot, economy, buildings, upgrades, golden cookies, menu, expansions, prestige, levels, cosmetics, offline, tech) plus the differences from the current build, with the full document in gdd.md next to it. Source of truth for the game's vision; preloaded by every bakery-team agent.
---

# Game design (summary)

The user's game design document (GDD) is the **source of truth for the game's vision**: briefs and features must not contradict it. This is a summary to keep every agent's context small. **Before designing or building anything that touches a section, read that section in full** in `gdd.md` next to this file (`${CLAUDE_PLUGIN_ROOT}/skills/game-design/gdd.md`, or `ls ~/.claude/plugins/cache/cookie-memory/bakery-team/*/skills/game-design/gdd.md | tail -1`). Read only the sections you need; use `grep -n "^##" gdd.md` to find them. All numbers are guideline values; the real ones live in `buildings.yml` / `upgrades.yml` (balance-designer).

- **§1 Concept:** an idle clicker played in the world, not a menu. Every player has their own plot, there is a hub with leaderboards, and you can visit other plots. Relaxed (no PvP), short and long sessions with offline baking, everything you buy is visible, and the server has its own resource pack and models.
- **§2 Lore:** warm, cosy and a little absurd bakery fairy tale. You inherit a run-down bakery with one cookie on a pedestal and end in the "Heavenly Bakery". Lore comes through holograms and level titles; there is no forced story.
- **§3 Plot:**
  - The starter plot is about 11×11 with fences: factory, pedestal with a floating 3D cookie you click, conveyor belt (more and faster cookies with CPS), stats holograms, and a shop panel.
  - Bought buildings appear physically, with a visual cap per type.
  - **Ingredient Farm (§3.3):** on hold since 2026-10-25 (no new builds; farm location parked). Ingredients and recipes are built without it: the one-time Recipe Book upgrade (~10K baked) starts ingredient production in the five ingredient buildings (flour, milk, sugar, chocolate, eggs); recipes are bought in a textured chest GUI (`/bakery recipes` or the Bakery Shop panel).
- **§4 Economy:**
  - Cookies, CPC (starts at 1), CPS. A building costs base × 1.15^owned, and there is no selling. CPS = Σ(base × count × milestone) × (1 + additive bonuses) × crowns × buff.
  - 11 buildings, from Wheat Field 15/0.1 to Portal Bakery 1T/10M, unlocked by expansion. Building 7 is the Chicken Farm (eggs), which replaces the Beehive.
  - Milestones give ×2 at 10/25/50/100/150/200, and the model changes too.
  - Click upgrades: +1 up to +500 CPC, then "Handy Fingers" (+1/3/5% of CPS per click).
  - Recipes: +2–5% CPS each, cost cookies + farm ingredients (flour, milk, sugar, chocolate, eggs), bought in the Recipe Book at the farm, reset on rebirth.
  - Golden cookies (from Expansion 2): every 2–5 min, gone after 15 s. Frenzy ×7 CPS 30 s (45%), Click Frenzy +777% 15 s (25%), Lucky (20%), Cookie Rain (10%). Buffs stack and none are negative.
  - The shop panel opens a chest GUI with tabs: buildings ×1/×10/×100/Max, clicks, recipes, expansion, prestige, statistics, cosmetics. Numbers are abbreviated (1.5K, 2.3M…).
- **§5 Expansions:**
  - 11×11 → 15×15 (10K) → 20×20 (500K) → 25×25 (25M) → 30×30 (1B, after rebirth 1) → 35×35 (100B, after rebirth 3).
  - Each one unlocks buildings and mechanics and is pasted with FAWE.
- **§6 Progression:**
  - Pacing runs from the first CPS within 5 min to rebirth 1 at about 6–10 h.
  - Rebirth needs Expansion 3 plus at least 10 new stars. Stars = round(10 × (lifetime/1B)^(1/3)), each worth +1% CPS/CPC permanently. It resets the run; stars, level, achievements and cosmetics are kept.
  - The star tree covers economy, head-start expansions, golden cookie and comfort/offline upgrades.
  - Baker level: lifetime cookies, need = 1000 × 1.35^(L−1), levels 1–100 with titles, +0.25% CPS per level, and a cosmetic every 5 levels.
  - Ascension (10 rebirths and 500 stars): crowns = stars/100, ×1.10 each multiplicatively, plus a crown tree.
- **§7 Extras:** Cookie Coins (cosmetics only); trails, belt, pedestal and hologram skins, villager hats, plot themes; achievements; daily orders, seasonal events, co-op later.
- **§8 Offline and fair play:** offline gives CPS × time × 50% for up to 2 h, improvable to 100% and 12 h, with a message on login. At most 15 clicks/s count. Everything is computed server-side.
- **§9 Tech:** plugins are CookieClicker, CookieCore, a resource pack loader, LuckPerms and FAWE. Per player it stores cookies (current, lifetime, this run), buildings, upgrades, plot level, stars/tree/rebirths, crowns, level, achievements, coins, cosmetics and last logout, in SQLite/MySQL with autosave.
- **§10 Open questions:** server name, plot storage, click entities, launch cosmetics, Ascension at launch, double vs BigDecimal.

## Differences from the current build
Maintained by the orchestrator. Each line is resolved by a future feature (then removed here).
- **Buildings (4.2, 4.3):** all 11 buildings and the milestones are built (building-roster, 1.2.0), with tuned values (e.g. Wheat Field 15 / 0.15, Baker's Apprentice 75 / 1). Unlocks use cookies baked instead of expansions until plot expansions exist. The shipped id for building 7 is still `beehive`; the Ingredient Farm feature renames it to the Chicken Farm (`chicken_farm`, with a save migration).
- **Plots are client-side (1, 3):** plots are admin-placed shared locations where every player sees only their own progress. There are no private per-player regions, so **visitor mode** is on hold.
- **Plot size (3.1, 5):** `factory-makeover` ships a fixed 31×30 fenced plot with a 19×14 factory; this document starts at 11×11 and grows to 35×35 through expansions. → a `plot-expansions` feature has to reconcile the factory size with the starter plot (smaller starter factory, or a bigger starter plot).
- **Shop (4.7):** the buildings and click upgrades are bought on in-world hologram panels and an upgrade shelf, not a chest GUI. The first chest GUI comes with the Recipe Book.
- **Ingredient Farm and recipes (3.3, 4.5), golden cookies (4.6), prestige (6), cosmetics (7), offline progress (8):** not built yet. Click upgrades (4.4) are built (upgrade-holograms).
