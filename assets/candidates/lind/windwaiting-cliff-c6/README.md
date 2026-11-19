# Windwaiting Cliff C6 — headland erosion and fracture study

Unapproved asset-local candidate on Draft PR #421. C1–C5 remain separate with their original manifests. The A/B/C seam convention uses +X alongshore, +Z up, −Y seaward and Z=0 as the provisional sea. Join by an X translation of 40. The 85-vertex matched section and periodic U seam remain in use.

## Geometry

The C5 sweep remains the editable carrier. C6 adds separate headland crowns and lost edges, skewed promontory shoulders, depth-specific collapse cuts, and shorter branches from the main joints. Each headland has its own cut depths, heights and inclination. The cuts attenuate or interrupt the strata according to the damage field. These features displace the real mesh. The deformation region stops before the shared seam transition. Crown relief blends to the inland plateau within five local units.

Additional collapse reefs cluster around the headlands and cove; the sea datum and talus support tests are run on the saved asset. Native procedural preview materials, the separate review water collection and the inherited independent inland terrain remain in place.

## QA and handoff

Machine QA reopens the master and checks all three closed tiles, the two joins, plateau slopes, inland nonperiodicity, module contacts and image decoding. The headland relief records use seaward rays on the reopened B mesh at four elevations. PNGs and the master are verified by SHA-256. Review uses the low perspective CG framing plus six supporting views. Judge the erosion silhouette, whether shelves still read as uniform stripes, and the balance between foreground grass, cliff faces, receding headlands and waterline debris.

G1 BLOCKED, G2 independent review NOT_RUN, full G3 and G4 NOT_RUN. World placement and formal adoption are pending. Production PBR and production water were outside this geometry pass.

The [official CG](../../../approved/game/cliff/sunset_background.png) is locked at SHA-256 `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`. No third-party images or geometry are included in this candidate.

[Master](windwaiting_cliff_C6_UNAPPROVED.blend) · [CG comparison](comparison.png) · [QA and hashes](qa.json) · [build log](build.log) · [reopen QA log](qa.log)

[Front](front.png) · [left](left.png) · [right](right.png) · [elevated](elevated.png) · [shore detail](shore_detail.png) · [sunset](sunset.png) · [low CG review](cg_review.png)

Run the C6 build, compare, and inspect scripts under `tools/map_blender/lind/` in that order. Use PyPI `bpy==5.2.4` for build and inspect, and Pillow and DejaVu Sans for comparison. Use a shared `--out` and supply the CG via `--reference` to compare and inspect.
