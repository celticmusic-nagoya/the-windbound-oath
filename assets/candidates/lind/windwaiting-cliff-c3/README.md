# Windwaiting Cliff C3 — inland-linked coastal bedrock

Unapproved asset-local review candidate. +Z is up, −Y is seaward and Z=0 is the provisional sea surface. World scale and placement are unapproved. The C1 and C2 directories and their hashes are preserved.

## Review scope

- **B1** The existing four-profile coastal sweep now connects continuously to a gentle inland skirt with its far edge and both end caps below the datum. Steep landward area above the datum is measured from the reopened mesh.
- **B2** Three staggered rounded headlands use overlapping curved plan lobes. Heights decline through the sunset view. The QA file records the authored headland widths and numerical curvature radii of the analytic coastline at the design stations.
- **B3** The exposed face has two projecting, separately shaped sandstone ledges with recessed intervening courses. The twelve block frames retain separate yaw and setbacks. Angle-based sharp edges preserve profile and block breaks. The thin profile shelves are mesh geometry.
- **B4/B5** Fifteen talus pieces use downward raycast contacts with upward normal Z at least 0.5. Twelve reef modules and two asymmetrical, layered sea stacks cross the provisional water datum. Stacks and reefs remain separate collections. Sea, light, and sunset camera are review staging.
- **B6** PBR detailing remains pending independent geometry review. The grass slot is limited to elevated upward-facing terrain.

## QA and known limits

The machine report records triangle areas clipped exactly at the datum, plus whole-body areas. In the second geometry build, the steep exposed inland-to-seaward ratio was 0%, and the exposed downward fraction was 7.03%. **The 15% whole-body downward-facing area criterion is unmet.** The whole-body ratio is 46.36%, including the large submerged underside used to keep the inland skirt closed. The alternative exposed metric does not replace the requested whole-body criterion. A change to the closure strategy would need a separate geometry decision.

The structural QA covers one closed component, boundary/nonmanifold edges, consistent winding, zero-area faces, nonadjacent triangle overlap, and saved-mesh module support. Independent G2 is NOT_RUN, G1 world integration is BLOCKED, and full game G3 and G4 are NOT_RUN.

## Provenance

- [Official sunset CG](../../../approved/game/cliff/sunset_background.png) is the primary visual reference. SHA-256: `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`.
- Cliffs of Moher geology and landforms were used as design guidance from the production instruction. External URLs furnished by that instruction were [Cliffs of Moher geology](https://www.cliffsofmoher.ie/unesco-global-geopark/conservation/geology/), [Burren and Cliffs of Moher Geopark](https://www.burrengeopark.ie/the-rocks-of-the-cliffs-of-moher/), and [Tourism Ireland](https://www.ireland.com/en/things-to-do/attractions/cliffs-of-moher/). The execution proxy denied access to those pages. No external photographs, stock geometry, or textures are included.

## Outputs

[Editable master](windwaiting_cliff_C3_UNAPPROVED.blend), [front](front.png), [left](left.png), [right](right.png), [elevated](elevated.png), [sunset](sunset.png), [CG comparison](comparison.png), [QA and output hashes](qa.json), [build log](build.log), and [reopen QA log](qa.log).

Run the C3 scripts under `tools/map_blender/lind/` in build, compare, inspect order. Build and inspect use the local PyPI `bpy==5.2.4` wheel with CPU Cycles. Compare uses Pillow with DejaVu Sans. Use the same `--out` folder and pass the official CG to compare and inspect via `--reference`.
