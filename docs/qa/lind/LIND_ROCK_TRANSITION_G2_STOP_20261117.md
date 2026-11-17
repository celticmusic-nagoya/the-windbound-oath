# LIND rock transition independent G2 STOP — 2026-11-17

## Actual execution
- Source PR #395: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/395
- GitHub Actions SUCCESS: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44042178508
- Artifact #14309199852 includes `rock_transition_study.blend`, `rock_transition_study.png`, `rock_transition_metrics.json`, `blender.log`.
- Render SHA-256 `5b9c41bd6c8c2acdf656d370e1d805e066fd3ebacb178b0f5595d4961dc2997d`.
- Blender SHA-256 `8ff2d54292badc07fffd8a222cb22932431fc08885eba8531ede2ba2ce4056e2`.
- Verified metrics: original source 8,570 vertices / 16,676 faces unchanged; transition 1,386 vertices / 924 quads; attachment boundary 462 edges. Separate open render-only object; no collision.
  
## Independent actual-image assessment
**G2 FAIL** for rock-to-terrain join. The added brown shell visibly resembles a concentric stepped skirt. Radial regularity, exposed horizontal bands, wedge-shaped facets and a sharp central spike dominate the result. These are not acceptable geological buttresses, natural soil or an integrated cliff base. Original gray scan rock detail remains useful and should be preserved.

## Root cause and stop decision
Three entire copies of the measured boundary were offset radially with global uniform layer distances and sinusoidal perturbations. This constructs a ruled ribbon, not geological structure. This is structurally the same family as failed procedural loft/profile methods (#389/#390), even if the boundary itself is scan-derived. **STOP this method; no small numeric retuning or repeated renders.**

## Different construction route
1. Preserve source scan and publisher UV/PBR.
2. Obtain properly licensed photogrammetry/rock support or authored hand-sculpted rock buttress components. Validate source scale, normals, texture resolution and license before use.
3. Author locally placed irregular rock masses, using the measured boundary as contact constraint only. No global boundary extrusion/ribbon.
4. Independently sculpt soil/turf top shelf; create a separate stable manifold collider and measure contact gaps/overlaps.
5. Three camera views, true PBR, visual QA at game size; G1 canonical scale and placement still BLOCKED.

## QA
G1 BLOCKED. G2 FAIL. G3 PASS for script execution, scan preservation, render and hashes only; open mesh not a collider and geometry quality FAIL. G4 NOT_RUN. No canon/main modification.
