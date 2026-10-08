# Lind Village — Player QA follow-up and STEP 8

Start: `8d3c7be521c207d6c3378426278ad4833b561dfc` (latest main fetched).
Scope: cow scale / Lind outdoor movement / Wind Stone assets and DEV staging only.
STEP 9 onward, formal map/story hooks, NPCs/Emma and battle changes are excluded.

## Follow-up checkpoint

- Cow: visible width 56 → 72.8 px (×1.30), same PNGs. Idle/walk bottom ground anchor retained; small pen extension accommodates sprite without crossing fence. Foot collision scales with cow.
- Pig 43 px and chicken 24 px, assets/behavior unchanged.
- Central `FieldMovement.settings`: outdoor pointer 4 → 5 px/frame; keyboard 18 → 22.5 px/input (×1.25). Original keyboard repeat model retained; no dash.
- Both paths use ≤2 px collision substeps. Pointer arrival clamps to exact destination; keyboard cancels old pointer movement; original world bounds retained.
- Interior/forest movement is outside this Lind outdoor adjustment and remains unchanged. No player walking animation exists to retime.
- Browser checks: PC 1280×720, landscape 844×390, portrait 390×844; actual livestock walk, 120s pen simulation, cow idle/walk foot anchor, unchanged other livestock, declared foot colliders, bridge crossing, water edge/dock, training gate/dummy click/tap/Enter, save guard and full preview restoration passed.
- Additional checks: thin obstacle cannot be skipped; world clamp, exact pointer arrival/no overshoot and keyboard/pointer interruption passed.
- Visual cow/fence/other livestock comparisons approved in all three viewport screenshots. Original livestock PNG bytes unchanged.

QA evidence: `qa/lind-step8/`.

## Wind Stone asset checkpoint

Three original standalone PNGs in `img/field/lind/landmarks/`:

| State | File | Size / mode | Fully transparent pixels |
|---|---|---|---|
| NORMAL | lind_wind_stone.png | 1312×1199 RGBA | 1,061,269 (67.46%) |
| GLOW | lind_wind_stone_glow.png | 1312×1199 RGBA | 977,356 (62.13%) |
| OFF | lind_wind_stone_off.png | 1312×1199 RGBA | 1,056,267 (67.15%) |

Normal generated from visually inspected approved village references; glow/off generated as edits of approved normal. Generator originals copied unchanged; no sheet cropping. Existing naming convention retained. All have alpha 0–255. Dark/light QA composites and original images visually checked: no black/white/checkerboard rectangle, no missing stone/pedestal/carvings/ivy. Same stone design, viewpoint and canvas; glow adds restrained mint rune illumination and nearby wind wisps/leaves; off retains undamaged unlit carved stone. Small generation differences in foliage/edges remain (not pixel-identical recolors); common canvas alignment is retained rather than rescaling by effect extent.

No existing field or battle PNG was replaced. Field PNG count: 65 (59 RGBA; 6 intentional opaque terrain tiles).
