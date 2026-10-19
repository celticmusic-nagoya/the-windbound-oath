# BG-02 / BG-03 battle background - preparation (index.html NOT connected yet)
Branch `feat/bg02-bg03-prep-claude`, base main `fe878573868dcf2a6b7c0a863dd0f66d550ed528`. Delivered originals on `assets/staging` are untouched; game copies live in `img/battle/backgrounds/`.

## Selection rules (area first, then enemy id) - `js/battle-background.js`
| background | applies to | how |
|---|---|---|
| BG-01 | `attackGob*`, `northGob*` | existing id rule, area independent (+ new foreground `bg_BG-01_fore.png`) |
| BG-02 | `mossSlime* forestBat* leafyBoar* forestGob* fieldGob*` **only when the battle is started from the moss forest** | `BattleBackground.noteArea(mapId, enemyId)` is called by the moss-forest hooks (`js/field/moss-forest-story.js`: onSymbol / onEncounter / onMonster) right before `startAttackBattle`. One-shot, bound to that enemy id, expires after 15 s. Same enemy in another area / without a note => unassigned (existing stage gradient). |
| BG-03 | goblin raider boss | `BattleBackground.applyRaider()` / `clearRaider()` build their own `#rbBg` / `#rbFg` inside `#raiderBattle`. NOT called yet. |
Note: the moss forest scene is hidden by `startAttackBattle` before the background is applied, so scene visibility cannot identify the area; hence the explicit note.
Dev entry `js/prologue-dev.js` (forestDevEnterA3 -> forestGob) has no note => no BG-02 (dev only; can be wired later).

## Layers
main (z0) -> units (z20/24) -> foreground (z27, **clipped to the lower band by `--battle-fg-top: 72%`**, pointer-events none) -> HUD/COMMAND/log (root level, above the stage). Main and foreground use the same box (`inset:0 -4% -14% -4%`), the same `cover` rule and the same position value, so no screen ratio shifts one against the other.
Measured finding: with the UNCLIPPED BG-02 foreground above the units, Aidan (default left position) is completely hidden by the trunk/ferns at PC size. Hence the band clip; only the ground-level band overlays feet. Faces/HP/HUD alpha coverage = 0.0 at PC / tablet / phone landscape / phone portrait.

## PNG normalization (`tools/art/normalize_fore_png.py`, audit in `docs/battle/bg02-bg03-png-normalize-audit.jsonl`)
Only pixels with alpha 0 get RGB 0; every pixel with alpha>0 is byte-identical (verified). Max alpha 254 is left as delivered.

## Still to do at integration (index.html, after P0-D / INT-02 are integrated)
1. `startRaiderBattle()` : add `window.BattleBackground?.applyRaider();` (after `#raiderBattle` display block); on raider end/cleanup: `BattleBackground.clearRaider()`.
2. Nothing else is required for normal battles (the existing `applyForEnemy(id)` call is reused). `index.html` cache-busting `?v=` for `battle-background.js` / `css/style.css` if the host uses it.
3. Re-run `tests/battle/bg02_bg03_background.py`, `bg01_background.py`, raider layout tests on the integrated tree; re-check the diff against the latest main.
