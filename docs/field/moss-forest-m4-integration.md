# Moss Forest M4 — index.html integration, save migration, legacy removal, warning lines

## Architecture
- `js/field/moss-forest-runtime.js` (`MossForest`): hosts A1→A2→A3 inside `#forestScene`. Map switching with fades, click + WASD movement (shared FieldNavigation/Movement/Collision/Camera/Culling), treasure, transitions, event zones, A3 seal, corruption symbols. Knows no story.
- `js/field/moss-forest-story.js` (`MossForestStory`): prologue bindings (stages 9–12, `PrologueProgress`, battles, Lou intro, altar, texts, treasure texts, save restore).
- `js/field/forest-warnings.js`: elder / Emma lines, branch = seal closed vs open (`PrologueProgress.count()>=3` or stage ≥13).
- `css/moss-forest.css`: placeholder visuals (real art = M5).
- Flags: `moss_a3_seal_open` (= 3 symbols defeated), `moss_a3_lou_found` (= `louFound`), `moss_a3_lou_rescued` (= stage ≥13). Collision of `cb_a3_seal` follows the flag live.

## Flow (index.html)
escape scene → `enterMossForest()` → A1 `from_cliff_fall` → A1→A2→A3 by exits → touch/click a symbol → `startAttackBattle` → victory → forest resumes → 3rd defeat opens the seal (visual dissolves, collision off) → sanctuary zone auto-starts the Lou intro → hidden wind path appears → altar trigger zone starts the altar scene. `tr_to_lind` is blocked during the prologue.

## Save schema (PrologueProgress)
- v2: `moss:{map,x,y,opened:[treasureIds],fired:[eventIds]}`; legacy `forestChests`/`position.fpx,fpy` are no longer written.
- v1 → migrated on load: chests fChest1/2/3 → `tr_a1_hollow`/`tr_a2_overlook`/`tr_a3_shrine`; position is derived from progress (0 defeats → A1 start, 1–2 → A3 entrance, seal open → just south of the seal, Lou found → sanctuary).
- v2 restore is validated: unknown map / non-finite / outside world / blocked / unreachable (32 px flood fill over live collision, so the closed seal is respected) → area entrance.

## Legacy forest
Removed in a dedicated commit: hand-placed DOM, chests, goblins, `louSeal/windPath/louSearch/louSprite/ancientStone`, their CSS/handlers/loop, `?legacyForest=1`. Encounter ids `forestGob1..3` remain as stable battle ids.

## Tests (need `python3 -m http.server 8765` in repo root + playwright)
- `tests/moss/m4_e2e.py` — through-play via index.html (entry, A1→A2→A3, closed seal, 3 battles, seal open, Lou intro, wind path, altar, node budget, console errors).
- `tests/moss/m4_save.py` — v2 round trip, v1 migrations, hostile/inconsistent saves, version rejection.
- `tests/moss/m4_npc.py` — elder/Emma lines and branch. `tests/moss/m4_devjump.py` — every DEV jump entry.
- Earlier: `seal_a3.py`, `walk_map.py`, `scatter.test.js`, `tests/field/m0.test.js`.

## Placeholders / open items
- Player/Fiona/Lou/symbol/seal/chest visuals are placeholders (M5). Treasure rewards are text-only (legacy parity); non-legacy chests say "（報酬は仮）".
- Emma has no formal conversation path yet: her lines fire on the DEV review interaction event only. The elder is a clickable placeholder inside 長老の家.
- Frame-rate-dependent speed (120 Hz) remains a separate task.
