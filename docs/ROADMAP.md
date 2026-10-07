# ROADMAP.md

## Baseline
v0.66 is the handoff baseline. It already contains a playable Prologue-oriented prototype and an increasingly polished battle presentation.

## Phase 1 — Stabilize the repository
Priority: highest.

- Audit active HTML/CSS/JS and identify legacy battle paths.
- Remove dead duplicate battle UI only after proving it is unused.
- Normalize asset paths under `img/`.
- Keep GitHub Pages deployment working after every change.
- Add a lightweight development/version indicator.
- Establish reusable constants/config rather than scattered magic values.
- Keep DEV Event Jump and one-hit kill gated.

Definition of done:
- No duplicated visible battle actors/HUDs.
- No stale battle logs.
- No broken asset paths.
- Desktop + Android responsive smoke test passes.

## Phase 2 — Finish battle impact presentation
- Raider HUD fully separated from the giant sprite.
- Damage numbers.
- Short hit-stop.
- Tuned screen shake.
- Normal attack slash effect.
- Fiona magic/healing effect.
- Distinct 「一閃」 effect.
- Hit/KO timing synchronized with animation.
- Avoid excessive effects that obscure readability.

Definition of done:
- Aidan/Fiona/Tainted Goblin/Raider actions are visually readable.
- KO art reliably swaps before/at victory.
- Victory overlay retains the correct battle background.
- No HUD moves with lunging actors.

## Phase 3 — Battle engine cleanup
Incrementally introduce:
- BattleActor model
- Action definitions
- target rules
- KO/revive
- centralized item usage
- status/resource update
- action queue
- SPD-based ordering
- Lou support hooks
- encounter metadata

Do not alter approved Raider difficulty while doing this.

## Phase 4 — Four-active party foundation
- Roster of six.
- 4 active / 2 reserve.
- Party selection UI.
- Story-required/restricted members.
- 100% EXP for recruited reserves.
- Lou separate SUPPORT slot.
- UI scalable to four actor HUDs.

## Phase 5 — Full save/state
Versioned localStorage schema:
- story progress
- current scene/map/position
- party roster/active formation
- levels/EXP/stats
- HP/MP/TP where appropriate
- inventory/equipment
- quest state
- treasure/event flags
- Lou/fairy progression
- settings

Add migration/default behavior.

## Phase 6 — Prologue content polish
- Verify full opening-to-Arthur-Fort route.
- Improve field collision.
- Check peaceful/burning Lind continuity.
- Complete side-quest state persistence.
- Moss Forest encounter/treasure persistence.
- Tune tutorials.
- Add audio hooks without blocking gameplay if assets are absent.
- Remove temporary visual artifacts.

## Phase 7 — Portfolio-quality presentation
- Title/intro polish.
- Settings/accessibility.
- Audio controls.
- Fullscreen behavior.
- Loading/preload strategy.
- Responsive typography.
- Keyboard/touch focus states.
- Performance pass.
- GitHub Pages release build without DEV tools.

## Phase 8 — Chapter expansion
Only after Prologue systems are stable:
- Chapter 1 capital
- Chapter 2 Elfen forest / Griffon
- Morwen interlude
- Chapter 3 Druid ruins / stone guardian
- Liam/Morwen/full roster recruitment
- dwarf/forging
- dancer/DANCE CHAIN
- BREAK
- combo techniques
- Lou FAIRY BLESSING survivor content

## Phase 9 — Multi-party signature systems
- Party A/B/C state.
- independent positions/events.
- party-switch UI.
- fortress-defense prototype.
- gate durability/waves/enemy advance.
- role-specific strategic actions.
- Lou global support.

## Suggested immediate Codex task
Start small:
1. Read `AGENTS.md`, `docs/GAME_DESIGN.md`, and this roadmap.
2. Inspect v0.66 battle DOM/CSS/JS.
3. Fix Raider HUD placement without changing sprite scale or approved mechanics.
4. Audit the current impact-effects implementation.
5. Add/tune damage numbers + hit-stop only if the existing path is understood.
6. Test Tainted Goblin and Raider battles.
7. Report exact files changed and regression checks performed.

Do NOT begin with a wholesale framework migration or rewrite.
