# Overnight asset / rendering audit

Fresh remote main: `d3e299ac7ca90eb49629570a57a90ff678ad7591`.
Branch: `work/overnight-stability-audit`. Audit only; no application/image change.

187 images / 378,990,248 encoded bytes / 1,104,298,320 nominal decoded RGBA bytes
(1,053.14 MiB). 176 RGBA / 11 RGB. No unreadable images or exact SHA-256 duplicates.
CSV contains every file, dimensions, mode, alpha/partial transparency, size, hash,
reference provenance, tags, visual review and size flags. Threshold flags are
screening aids (>2 MiB, axis >2048, axis <64), not quality verdicts.

All static image literals exist; all 178 runtime registry/request paths exist.
Embedded / numbered legacy / old Lou references: 0. Embedded directory absent.
Reference registries and content-bounds metadata count as references, not proof of
visible production use. Nine files were not reached by audited sources/registries:
Aidan/Fiona alternate idle, Aidan reference sheet/alternate wind slash, Lou old
skill_heal, four Forest Bat frames. Retain every file; Bat is a future source asset.
The previous fisherman villager idle is superseded visually by twelve fishing
poses, although initial constructor metadata can still request it.

Visual contact sheets reviewed all 187 images against a contrasting green matte.
Opaque terrain tiles are intentional. Five Battle PNGs visibly retain a light
background: Aidan evade, item, oath_awaken, skill_charge, skill_wind_slash_alt.
Do not infer backgrounds from RGB alone: the issue is visible in the composite.
No backgrounds were removed. Thumbnail review does not certify every edge,
finger or effect; detailed art approval remains PLAYER QA.

## Character quality and HD classification

PC complaints are not explained by insufficient native NPC resolution. NPC images
force `image-rendering:pixelated`; Aidan uses `auto`. The camera uses one positive
world transform, with fractional CSS placement and small occupation animations.
DPR increases physical samples on mobile and changes perceived coarse edges.
Hidden frame rectangles are not rendered sizes: report CSV/JSON estimates use
existing asset scale metadata; visible frame live rectangles are also recorded.

At 1920x1080, camera 1.80, DPR1:

| Character | Native PNG | Full PNG screen rectangle | Source / physical ratio | Class |
|---|---|---|---|---|
| Aidan idle down |1536x1024|160.28x106.85|9.58|B|
| Emma |1182x1330|70.59x79.43|16.74|B|
| Boy |1291x1218|75.20x70.94|17.17|B|
| Farmer idle |1377x1142|117.18x97.18|11.75|B|
| Fisherman idle |320x235|115.20x84.60|2.78|B|

A = sufficient; B = rendering comparison recommended before source changes;
C = 2x source candidate; D = remake. General villagers: B, all are heavily
minified at the tested PC scales. Children: B, plus known static-pose movement.
Fiona field: NOT PRESENT (legacy CSS character is not a production field PNG).
Aidan: B for fractional/compositing comparison, not a proven source defect;
Emma/farmers/villagers: B for nearest-neighbor minification comparison. Fisherman:
B for the PC complaint; conditional C if future 2.10x/DPR3 native detail is required
(physical/source 1.26x there). No remake or mass upscale is justified by this audit.

All 17 scales in five viewport/DPR conditions are recorded (85 cases, 3825 frame
rows). Required representative scales 1/1.5/1.8/2.1 are included. Compare rendering
in an opt-in QA branch before deciding aesthetics. Do not import changes from the
separate character-HD or Battle Motion prototype branches.
