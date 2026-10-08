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

Pending STEP 1 checkpoint.

## STEP 3 — farm facilities

Pending STEP 2 checkpoint.

## STEP 4–15

Not in this first batch. Animals, nature/props, bridge/fishing, training assets,
windstone, villagers, Emma, environmental animation, final map/event integration,
wind-stop behavior, peaceful full regression and attack assets remain sequential
later gates. Battle engine, actor state/motion, all existing battle PNGs and save
schema are unchanged.
