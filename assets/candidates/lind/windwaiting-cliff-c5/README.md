# Windwaiting Cliff C5 — A/B/C coast assembly

Unapproved provisional review candidate on Draft PR #421. C1–C4 and their recorded SHA-256 values remain in their original directories. C5 continues the approved production approach for joinable cliff strips.

## Shapes and seams

A, B and C are individually editable closed meshes. The three variants use different headland stations, cove centers, crest heights and shifted fractures. Their geometry hashes serialize local vertex coordinates and polygon indices. The assembled inspection scene uses A–B–C at X offsets −40, 0 and +40. Each tile inherits 85 ordered connection vertices at local X=−17 and +23, with +X tangent and U advancing by one tile. Custom boundary normals use the shared section. The QA reports their measured angular error after Blender reopens the file.

Crest heights taper into the shared profile over 15 provisional units. The saved plateau slope is sampled along the first and last 8 units of every tile. Long geological bands have wedge-shaped terminations, continue through the shared seam profile, and use independent elevations and small dips. The nominal authored shelf projection is 0.225 local units. Readability and apparent shelf length in the low view remain independent art-review questions.

The inland context matches each coastal back edge at the join. Its height field blends to an independent two-dimensional low-frequency surface over 12 units of inland distance. The report compares reopened terrain heights at offsets of 40 units alongshore to test against C4's exact periodic repetition.

## Staging and checks

The low CG camera looks along the coast from near plateau height. Its projected cliff-height metric is a geometric projection measurement at three authored stations. Review light uses a cool fill and brighter sky. The sunset and low CG cameras use warm review lighting. The sea is a separate staging collection. Reef groups include submerged pieces, and talus contact and detached stack datum tests use the reopened scene. Standalone production water and seabed are separate work.

The production CG at [sunset_background.png](../../../approved/game/cliff/sunset_background.png) is the visual source. Its SHA-256 is `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`. The stage uses original geometry and procedural preview materials. Production PBR, official world placement, game-camera QA and performance remain pending. G1 BLOCKED, independent G2 NOT_RUN, full game G3 NOT_RUN, G4 NOT_RUN. The structural subset is reported for the three individual closed tiles.

[Blender master](windwaiting_cliff_C5_UNAPPROVED.blend) · [comparison with official CG](comparison.png) · [reopened QA and SHA-256](qa.json) · [build log](build.log) · [QA log](qa.log)

[Front](front.png) · [left](left.png) · [right](right.png) · [elevated](elevated.png) · [shore detail](shore_detail.png) · [sunset](sunset.png) · [low CG review](cg_review.png)

Run the C5 build and inspect scripts under `tools/map_blender/lind/` with local `bpy==5.2.4`; run comparison with Pillow and DejaVu Sans. Use the same `--out` path for all steps and supply the official CG via `--reference` to comparison and inspect.
