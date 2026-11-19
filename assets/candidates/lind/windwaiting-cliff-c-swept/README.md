# Windwaiting Cliff C — first swept-mesh candidate

**Status: unapproved candidate.** The coordinate space is asset-local and provisional. Up is +Z, seaward is −Y, and Z=0 is the provisional shoreline datum. The closed body extends below that datum. World scale, placement, game cameras, and integration remain gated.

The visual source is [the approved sunset CG](../../../approved/game/cliff/sunset_background.png), Git blob `085b8d476d9eedb748ca9bd215b162e8f7dfa6e6`, SHA-256 `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`. The [comparison sheet](comparison.png) pairs the complete CG with the four ungraded studio renders. Lighting and cameras were chosen to expose the asset geometry.

The base mesh sweeps an authored shore-to-inland closed profile along eighteen nonuniform coast stations. Rock shelves, joint recesses, the projecting shoulder and sea-cut notch are part of the editable mesh. Two detached stacks and fifteen talus objects live in separate collections. The prior scan-based C and macro pipeline candidate remain independent.

## Outputs and verification

- Editable [Blender master](windwaiting_cliff_C_swept_UNAPPROVED.blend), plus [front](front.png), [left](left.png), [right](right.png) and [elevated](elevated.png) renders.
- [Machine QA](qa.json), [build log](build.log) and [reopen log](qa.log). Local `bpy` 5.2.4 LTS, CPU Cycles, process exit 0.
- Cliff body has 13,981 vertices and 13,942 faces in one closed connected component. There are zero boundary, nonmanifold or inconsistent-winding edges and zero zero-area faces. BVH overlap on the reopened tessellation found zero intersecting nonadjacent triangle pairs. The body check excludes the separate stacks and talus. The report also records local bounds and representative overhang and recess coordinates.
- All PNGs decoded. The four review views are 1200×760, and the report contains sizes and SHA-256 for the master, the four views and the comparison. The master was reopened with scripts disabled.
- G1 **BLOCKED** on canonical world scale and placement. G2 **NOT_RUN** for independent art review. The structural subset of G3 **PASS**. Full G3 **NOT_RUN** for game UV, LOD and export validation. G4 **NOT_RUN**.

## Independent art review

Compare the CG and the asset for the continuous plateau silhouette, the stepped headland, the steep drop, the depth and spacing of vertical joints, the strata and wave-cut shelf. The first renders show section end caps, pronounced joint channels and simplified turf. Review their impact on the silhouette and geological continuity before further detail, material, or integration work. Review the separate sea stacks and talus for scale at the intended game camera after its approval.

## Reproduction

Run the build and inspect scripts in `tools/map_blender/lind/` with a Python environment containing `bpy==5.2.4`. Run the comparison script with Pillow and DejaVu Sans. Pass the same `--out` directory to all three scripts and pass the original CG to the comparison and inspect scripts using `--reference`. Run in build, compare, inspect order. The scenes use procedural materials and have no external texture files.
