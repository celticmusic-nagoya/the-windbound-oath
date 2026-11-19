# Windwaiting Cliff C7 — regional collapse and promontories

C7 is an unapproved candidate for Draft PR #421. C1–C6 and their binary manifests remain archived. It uses asset-local coordinates with +X alongshore, +Z up, −Y seaward, and the provisional sea at Z=0.

## Geometry decisions

The [preproduction observations](observations.md) relate the approved CG and Cliffs of Moher land, oblique, and near-water photo previews to the geometry. Distinct A/B/C bodies retain the C6 seam convention. After the protected transition each tile has three separate nonperiodic landform controls with different left and right spans, crest changes, plan displacements, slip scars, and debris apron projections. The main tile has a high broken near head, a lower and deeply recessed middle domain, and a less massive far spur. Shelves are eroded in the slide scars, with stratum positions shared outside damaged areas. Review water and inland context remain separate from the editable cliff strips.

Fourteen additional debris rocks group around the near head, middle cove, and far spur. Fifteen cliff-foot talus pieces use upward mesh contacts; the reopened QA checks the supporting normal and waterline intersections for the other rocks. The first contact search missed the new apron and stopped. The final search samples a wider foot band vertically and checks only upward support.

## Review and validation

The primary review camera is low and looks along the shoreline from an oblique seaward position. The earlier position hid both the middle and far samples. The final position shows at least some sampled cliff face in every region, reported separately from framing and projected cliff-height measurements. Geometric ray counts do not decide independent silhouette or aesthetic QA.

[Master](windwaiting_cliff_C7_UNAPPROVED.blend) · [comparison](comparison.png) · [QA and SHA-256](qa.json) · [build log](build.log) · [QA log](qa.log)

[Front](front.png) · [left](left.png) · [right](right.png) · [elevated](elevated.png) · [shore detail](shore_detail.png) · [sunset](sunset.png) · [low CG review](cg_review.png)

The three closed bodies, their seam UV and normal continuity, and slopes are evaluated after reopening. G1 is BLOCKED, independent G2 and full G3/G4 are NOT_RUN, and the general inland-facing area proxy retains the hidden closure contribution. Headland crown radii are still reported. The leading local cut reduces that radius against the old rounded-tip proxy and is a point for independent review.

Reproduce via the C7 build, compare, and inspect scripts under `tools/map_blender/lind/`. Use `bpy==5.2.4` for build and inspect and Pillow with DejaVu Sans for compare. Give all tools the same `--out` path and the comparison and inspection tools the approved CG via `--reference`. PBR and production water remain outside this geometry pass.
