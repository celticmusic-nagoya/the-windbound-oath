# Lind field production — first batch (STEP 0–3)

Start main: `b0e90369271f868c5bf04ca9bd75f1bdd66c5a6d` (fresh fetch).

## STEP 0

Eight ZIP images received and visually inspected. Originals and SHA-256 inventory:
`docs/art/reference/lind/`. Map, catalogue, detailed inn, terrain/water, training,
villagers, Emma design and Emma sprite reference verified. Sheets are never cropped
into production sprites. Emma production remains STEP 10, after NPC scale STEP 9.

## STEP 1 — terrain

Seven individually generated PNGs: grass, dirt, cobblestone, grass/dirt edge, water,
riverbank, cliff. Images are newly drawn with the actual reference image supplied
to image generation. Six ground textures intentionally fill their canvas (RGB);
cliff is RGBA with 1,065,632 fully transparent pixels (67.75%). Ground's lack of
alpha is intentional, not a baked unwanted backdrop. No white/black/checkerboard
backdrop or sheet neighbours seen in the visuals. Reference sheets are not runtime
assets. File dimensions, actual alpha counts and hashes: `lind-asset-audit.json`.

Temporary **in-game DEV placement**, launched from DEV → リルド村・素材仮配置,
reuses original field camera, click/tap destination, arrow/WASD movement and river/
bridge collision. Original room and field position are restored on exit. No DEV
Jump, story flags, quests or save are modified. Roof/body collision applies only
in review. Live prototype placements remain intact pending full STEP 12 map
integration; review positions preserve the confirmed geographic relationships but
are not finalized playable map coordinates. Original CSS player is the existing
scale comparator, not a newly claimed official player sprite.

1280×720, 844×390, 390×844: assets load, camera/movement, water blocked, bridge
walkable, cliff foot collision, art review open/exit restore, unchanged story/save,
training battle after exit PASS. Image 404=0, JavaScript exceptions=0.

Warnings: generated source textures are high-resolution, not native 32×32 tiles.
Repetition and grass/path palette transitions require final-map polish at STEP 12;
this checkpoint does not claim exact pixel-continuous autotile edges. The bridge is
still the original prototype; formal bridge/fishing production is STEP 6. The
reference's diagonal river topology is also reserved for STEP 12.

## STEP 2 — major buildings

Ten standalone RGBA PNGs generated: inn, item shop, elder house, Aidan house,
four residential variants, barn, storage. Each has real transparent pixels, with
no baked backdrop/sheet neighbours or major roof/door damage seen in alpha
composites. Three viewports tested: each image decoded/displayed, each foot
collision blocked, front approach walkable, review state restored and training
battle still playable. Source generation resolution is retained without PNG
processing. World positions are DEV placement only; residential assignment to
Emma/Fiona and room/event integration remain later gates. Grounded object depth
uses foot Y; an object selector allows quick inspection. Images load lazily so
inactive review does not eagerly fetch all field art. Review refuses to open
during combat/attack progression, preserving live battle behavior.

STEP 1 commit: `bd299b8d79dca69063fe9af235dc1d7bab2e689a`.
Concurrent upstream `908fd63` (new Aidan cut-in PNG) was retained by rebase; no
battle image was overwritten. Original pre-rebase commit c8b1174 is superseded.

## STEP 3 — farm facilities

Eleven standalone RGBA PNGs generated: cowshed, pigsty, chicken coop, wheat,
vegetables, flowers, apple orchard, haystack, hay bale, cart and farm tools.
All have real alpha/transparent pixels; alpha composites visually checked for
backdrop/sheet fragments, missing roofs, crop edges, tool shafts and cart wheels.
Livestock shelters intentionally have no baked animals (separate STEP 4). Fields
are walkable ground decoration; structures/props use provisional foot collision.
`lind-content-bounds.js` records each PNG visible alpha bounds (>16). Render
positions/sizes normalize transparent export padding and preserve aspect ratio;
PNG bytes remain untouched. Foot collisions follow the normalized content height,
and the two orchard trunks use separate collision boxes with a passable gap.
Apple grouping contains two complete trunks and crowns. No human/animal/Emma
sprite was generated, so their anatomy/NPC scale/Emma QA is NOT APPLICABLE.

Three-viewports QA PASS: all 28 paths loaded, each lazy object decoded after
inspection focus, collision/front approaches, field click/tap and keyboard
movement, review close restoring position/room/player depth and original
collision, direct save blocked in review, seeded existing version29 save bytes preserved,
normal story/flags/storage untouched; crop plots and orchard trunk gap walkable.
Training remains playable after review, and review is rejected during battle.
Toolbar select key events do not move the player. No battle/PNG/stat/animation
source changed. Normal and Raider battle regression separately passed all three
viewports: COMMAND open/close, DEV kill during enemy action, terminal KO/Victory
and stale timer protection; Raider HP1250 and independent HUD retained.

STEP 2 commit: `17f45ba` (normally pushed to main).
Image 404=0; JS exceptions=0; runtime embedded/numbered/old Lou path refs=0;
embedded directory absent. Latest user cut-in image from `908fd63` unchanged.
Evidence: [QA results and screenshots](qa/lind-batch1/); alpha/hash audit and
`lind-production-manifest.json` include all 28 production files and reference
provenance. Per-gate tests ran before the next gate started.

## STEP 4–15

Not in this first batch. Animals, nature/props, bridge/fishing, training assets,
windstone, villagers, Emma, environmental animation, final map/event integration,
wind-stop behavior, peaceful full regression and attack assets remain sequential
later gates. Battle engine, actor state/motion, all existing battle PNGs and save
schema are unchanged.

## Result and remaining warnings

**FINAL RESULT: PASS WITH WARNINGS — initial STEP 0–3 batch only.**

No manual asset review blocker found in the generated object visuals. Source
textures are not native 32×32; exact seamless/autotile border polish remains.
Field and NPC scale is provisional; the existing CSS player is only a comparator.
No final collision meshes, roof separation, curved river topology or room/event
remapping are claimed. Permanent playable village integration is STEP 12, not
this art-preparation gate. Full peaceful village/prologue playthrough and wind
stop/attack continuity tests remain STEP 13–15. Future normal NPCs/Emma/animals
have not been declared tested or complete.

| STEP | Status |
|---|---|
| 0 source/reference audit | PASS; all 8 references verified |
| 1 terrain | Produced 7; temporary placement QA PASS; tile polish warning |
| 2 major buildings | Produced 10; alpha/visual/placement QA PASS |
| 3 farm facilities | Produced 11; alpha/visual/placement QA PASS |
| 4 animals | Deferred; next authorized production gate |
| 5 nature/props | Deferred |
| 6 river/bridge/fishing | Deferred |
| 7 training | Deferred; current event protected |
| 8 windstone | Deferred |
| 9 villagers/NPC scale | Deferred |
| 10 Emma | Reference/canon verified; generation deferred until STEP 9 |
| 11 birds/environment | Deferred |
| 12 final map integration | Deferred; original playable map retained |
| 13 wind stop | Deferred |
| 14 peaceful full regression | Deferred; current limited smoke passed |
| 15 attack preparation | Deferred |

Next: STEP 4 standalone livestock with anatomy/scale QA, then sequential gates.

## Changed files

Runtime wiring: `index.html` (one field review stylesheet, three field scripts).
New field-only files: `css/lind-field-review.css`, `js/field/lind-assets.js`,
`js/field/lind-content-bounds.js`, `js/field/lind-review.js`. No change to
`css/style.css`, battle CSS/JS, `js/assets.js`, PartyManager or save schema.

Production PNGs: `img/field/lind/terrain/` (7), `buildings/` (10), `farm/` (11).
Reference originals: `docs/art/reference/lind/` (8 PNGs + inventory), never used
as cropped runtime sprites. Documentation: source audit, this report, asset
alpha/hash audit, production provenance manifest, QA JSON/screenshots and
`docs/story/prologue-character-canon.json` (Emma references now visually verified).
Deleted files: none. Existing battle images changed by this batch: zero.
