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

## DEV integration and final QA

- New `LindFieldWindStone` actor: independent NORMAL/GLOW/OFF image state, shared 95 px visible width / ~124.45 px height and common PNG canvas alignment. Center plaza temporary position x695/y490. Landmark is taller than 34×44 placeholder player, smaller than houses.
- Physical foot/pedestal collider [14,100,70,23] relative to anchor is identical in every state. Glow wisps, transparent padding and decorative leaves are not collision. Four surrounding approaches remain walkable; walking into the base stops.
- Three decorative leaf nodes animate independently of static stone. Reduced-motion removes their animation. No particle animation drives events or actor state.
- DEV select switches all three states. OFF sets environmental wind OFF; wind toggle OFF forces unlit stone/no particles and pauses existing grass/leaves/laundry/sign wind motion. ON restores last selected NORMAL/GLOW. Water background animation and livestock continue independently.
- Click/tap/Enter interaction requires proximity and emits `reviewOnly` field interaction, provisional DEV text only. No formal event/progression/save changes. Preview exit clears interaction and restores live position/state.
- Stone focus places player beside the landmark; full stone remains visible below DEV controls on landscape, including interaction notice. No horizontal page overflow in any viewport.
- Map-edge follow-up: an unreachable pointer destination stops when a clamped step cannot advance; no lingering movement target.

| QA | PC 1280×720 | Landscape 844×390 | Portrait 390×844 |
|---|---|---|---|
| Cow/fence scale, idle/walk, bounded motion | PASS | PASS | PASS |
| Keyboard/click or tap, colliders, bridge, dock, gate, dummy | PASS | PASS | PASS |
| Stone 3 states, alpha/scale/whole-object visibility | PASS | PASS | PASS |
| Stone foot collision, walkaround, click/tap/Enter | PASS | PASS | PASS |
| Wind OFF, water continues, reduced motion | PASS | PASS | PASS |
| Preview restore and save protection | PASS | PASS | PASS |
| Four house entrances/exits, fishing NPC, Aidan/Fiona actual attack + manual target input | PASS | PASS | PASS |
| Existing tutorial trigger, registered battle assets, boss HUD | PASS | PASS | PASS |
| Normal/Raider COMMAND, enemy motion, DEV kill, KO/Victory/race protection | PASS | PASS | PASS |

147 protected source/image files compared byte-for-byte against start: zero changes. Existing field content bounds unchanged (56 entries); new entries only. Inline code from interior movement through battle implementation unchanged. Raider HP1250 and independent giant sprite/HUD geometry match prior batch QA.

Technical checks: image 404 = 0; JavaScript exceptions = 0; console errors = 0 in final viewport tests. Battle registered paths 61/61 loaded. Old embedded / asset-number / support/lou references = 0; embedded directory absent. DEV_MODE=true retained.

## Warnings / stop point

- DEV staging only; formal village map, story wind-stop and field character/NPC sprites remain future work, by instruction. Existing placeholder player is retained.
- Stone state variants preserve design/canvas/pose but have small generated edge/foliage variations; not pixel-identical recolors. No clipping or visible scale jump detected. Player visual approval remains the next gate.
- Existing terrain remains high-resolution artwork; original production 32 px/native-scale policy still awaits later formal map/character scale QA. No destructive downsampling was done.
- No MANUAL ASSET REVIEW REQUIRED / missing asset items. No STEP 9+ started.

Final judgment: **PASS WITH WARNINGS — PLAYER QA READY**.

## Checkpoints / changed files

- Follow-up: `b35c748ec3c6b57ec058739ae5d61969e3ce9090` — normal push confirmed.
- Assets: `a2a0c476508fbc0af216ee2158a555174e775577` — normal push confirmed.
- Final DEV integration/QA: final HEAD (reported with full hash after normal push).

Production changes: `index.html` field movement hookup only; `js/field/field-movement.js`, `lind-animals.js`, `lind-content-bounds.js`, `lind-environment.js`, `lind-review.js`, new `lind-wind-stone.js`; scoped `css/lind-field-review.css`; three new landmark PNGs. Metadata/report changes: `docs/field/lind-asset-audit.json`, `lind-production-manifest.json`, this report, and `qa/lind-step8/` evidence/scripts. No deleted production assets.
