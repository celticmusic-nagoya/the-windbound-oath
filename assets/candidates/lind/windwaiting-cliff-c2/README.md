# Windwaiting Cliff C2 — faceted coastal bedrock

Provisional asset-local coordinates. +Z is up, −Y faces the sea, and Z=0 marks the provisional sea surface. World scale and placement remain unapproved. C1 and its SHA records are preserved in their original directory.

## Changes from C1

- Twelve main rock facets use local widths 1.55–2.90, separate yaw and setback, and four authored section families. Three deep joints occupy irregular positions. Connecting transition strips preserve the single editable cliff body. The reported joint fraction and spacing are design metrics from the authored breakpoints; independent visual QA should judge how they read in the renders.
- The coastline bends around two headlands and a recessed cove. The plateau has a continuous nominal 5.2° seaward gradient with gentle elevation variation. End caps are below the provisional sea surface. The wave-cut shelf narrows and submerges, and block profiles extend through the lower face.
- Fifteen talus rocks use three original mesh families and cluster on upward-facing cliff-foot surfaces. The saved Blender geometry is checked with downward ray casts. Two detached pillars intersect the provisional sea datum. No external rock assets are used.
- The fifth view uses a warm review light and an oblique camera for comparison with the approved CG. This is a review camera; the game camera and PBR detail pass remain gated.

## Review files

- [Editable Blender master](windwaiting_cliff_C2_UNAPPROVED.blend)
- [Front](front.png), [left](left.png), [right](right.png), [elevated](elevated.png), and [sunset review](sunset.png)
- [Official CG comparison](comparison.png), [machine QA and file SHA-256](qa.json), [generation log](build.log), [reopen and QA log](qa.log)

Compare the silhouette, cove depth, block-to-block plane changes, seam readability, base contact and the breakup of the wave-cut shelf. The simple materials and sea surface are review staging. Independent G2 and full game G3 remain NOT_RUN. G1 world integration is BLOCKED and G4 is NOT_RUN.

## Reproduce

Run `build_windwaiting_cliff_C2.py` and `inspect_windwaiting_cliff_C2.py` with `bpy==5.2.4` and run `compare_windwaiting_cliff_C2.py` with Pillow and DejaVu Sans. Use the same `--out` folder for all three tools and the approved CG as `--reference` for compare/inspect. Run in build, compare, inspect order.

Source CG: [approved sunset background](../../../approved/game/cliff/sunset_background.png), SHA-256 `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`.
