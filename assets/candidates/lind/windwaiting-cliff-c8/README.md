# Windwaiting Cliff C8 — fracture panels and scar debris

Unapproved candidate in Draft PR #421. C1–C7 remain archived. C8 preserves the C7 coast, headland silhouettes, primary camera and provisional coordinate system, and concentrates on the exposed rock face. +X is alongshore, +Z up, −Y seaward, and Z=0 is provisional sea level.

Eleven individually authored panels have pitched faces, asymmetric rakes and different top and bottom limits. Recessed panels interrupt the inherited bed projections, and preserved shelves bend locally into the inclined joint planes. The deformation is compactly supported inside each tile. A/B/C keep their matched 85-vertex cross-section, UV period and seam transition.

Twelve new waterline rock modules use four shared alongshore scar anchors. QA records their saved positions, offsets from the scars and waterline state. The separate C7 talus is still checked with downward support rays. Reef intersection with the provisional water datum provides a waterline check; offshore seabed contact is not assessed at this stage.

[Reference observations and rights](observations.md) · [Blender master](windwaiting_cliff_C8_UNAPPROVED.blend) · [Official-CG comparison](comparison.png) · [QA and hashes](qa.json) · [build log](build.log) · [reopen QA log](qa.log)

[Front](front.png) · [left](left.png) · [right](right.png) · [elevated](elevated.png) · [shore detail](shore_detail.png) · [sunset](sunset.png) · [low CG review](cg_review.png)

The machine tests cover each closed tile, the joined boundaries, transition slopes, reopened cliff relief, landmarks visible from the unchanged low camera, PNG decoding and SHA-256. Panel readability when the image is reduced, the visual interruption of the main shelves, and the reading of debris in the composition remain independent art-review questions. G1 BLOCKED, G2 NOT_RUN, structural G3 subset recorded in QA, full G3/G4 NOT_RUN. Vegetation detail, PBR, and production water are separate passes.

Run the C8 build, compare and inspect scripts under `tools/map_blender/lind/`. Build and inspect use `bpy==5.2.4`; compare uses Pillow and DejaVu Sans. Supply a common `--out` and use the approved CG as `--reference` for compare and inspect.
