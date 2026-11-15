# MORWEN-EYELID-07 — topology-first recovery plan (AUDIT / DESIGN ONLY)

Status: PROPOSAL; not canonical, not an adopted mesh. Scope: diagnostic design for the EYELID-05/06 candidate and reusable face-part production pipeline. No edits to existing assets, mesh, shape keys, main, or published files.

## Evidence (verified in repository)
- `inspect_lid_geometry_06.py`: selects lid margin edges by adjacent wall/patch polygons and `elm_patch` tags, and exports world XYZ and graph degree. It does **not** yet order a curve from inner to outer canthus, classify upper/lower, or establish stable vertex correspondence.
- `apply_corrective_06.py`: uses a different `len(adjacent)==1` boundary-edge criterion, interpolates 2D `y_px` by horizontal projection, applies Z-only deltas and radial distance falloff, and has an explicit guard against saving an unvalidated model. Therefore this is not a proven 3D closure.
- The fetched `apply_corrective_06.py` contains literal `\\n` sequences embedded in code lines (outside strings); run `python -m py_compile` to confirm syntax before any Blender execution. Do not silently enable `EYELID_06_ALLOW_UNVALIDATED_DEFORMATION`.
- Camera real-model QA: Actions run 43658409668, head d833102, job success, 7 presets/4 orbits, 4 meshes unchanged, original .blend hash preserved. This proves non-destructive camera integration, **not** eyelid closure or visual art quality.
- EYELID-05 diagnostic still reports `eyes_hidden_when_closed=false`, `corner_no_flip_required_states=false`, `patch_relative_required_states_ok=false`. Retain existing failed trial ledgers; do not repeat the two stopped deformation families.

## Root-cause categories
1. Topology: no single canonical vertex-ID/edge-chain correspondence for upper and lower margins; differing extraction predicates.
2. Geometry: a 2D projected curve cannot uniquely define 3D depth, thickness, normals, or occlusion.
3. Deformation: key interaction Blink/Joy/winks needs independently validated delta composition, not one global displacement.
4. Rendering/QA: scene camera preservation is verified; visual image output and independent art comparison remain unverified. Separate build, geometric checks, render, and art review.

## Stage A — deterministic topology capture (read-only)
- Reconstruct the same EYELID-05 input .blend; record input SHA, Blender version, source reference hashes, object transforms, mesh vertex count, shape key names and index order.
- On the `Face` mesh, use `elm_patch` and polygon adjacency to classify **patch inner margin**, **patch outer ring**, and **side walls**. Use ONE shared extraction function for diagnostics and deformation.
- Build a half-edge graph from selected boundary edges. Assert one connected chain per designated upper/lower margin (or explicitly classify a closed loop), no forks, no duplicates, no zero-length edges. Do not sort vertices solely by X.
- Determine medial/lateral canthi using eye-local basis and recorded source calibration, not world-X sign assumptions. Traverse ordered vertices from medial to lateral; assign normalized cumulative 3D arc length `u`. Derive corresponding upper/lower samples by monotone arc-length interpolation and record vertex IDs, edge IDs, face IDs, rest positions, tangent, surface normal, eye-local frame, and skin/eyeball clearance.
- Produce `LID_TOPOLOGY_MAP.json` with explicit status `DIAGNOSTIC_NOT_CANON`. Reject ambiguous classifications instead of guessing.

## Stage B — geometry-first closed-eye candidate
- Define closed-eye target as a smooth 3D spatial curve in an eye-local frame, anchored at BOTH canthi, with independently constrained Y/depth and Z/height. 2D art curve is a projection constraint only.
- Map upper and lower chains onto the shared curve by arc-length; constrain upper/lower seam gap, canthus tangents, surface continuity, thickness, normals, no flipped faces, eye visibility, and no socket exposure from front, +/-45°, profile.
- Preserve all unaffected vertices and 56 original shape keys exactly; candidate corrective layers must be additive and reversible, with explicit per-expression collision checks for neutral, Blink, Blink_L, Blink_R, Joy, Blink+Joy.
- Do not enable current unvalidated-deformation bypass. If correspondence or source calibration is ambiguous, block geometry generation and request targeted art/sculpt review instead of inventing coordinates.

## Stage C — reproducible rendering & QA
- Separate jobs: 1) source rebuild, 2) topology diagnostics, 3) geometry candidate, 4) numeric QA, 5) deterministic orthographic render matrix, 6) independent art review. Each stage emits JSON with source SHA, tool version, parameters and deterministic seed.
- Render fixed views: front, left/right 45°, left/right profile; expression states neutral, Blink, Blink_L, Blink_R, Joy, Blink+Joy. Include close-up and final game-size 128/64/32 px composites on a nonblack background.
- Store images and SHA manifest in GitHub Actions Artifact. An Actions success or camera QA success must NEVER be reported as G2 art PASS.
- Gate G1 reference protection; G2 independent art review; G3 topology/depth/occlusion/shape-key technical QA; G4 game performance/Android separately. No main merge until approved.
- Use two attempts maximum per method family. After two failures, freeze evidence and switch to manually sculpted corrective targets or a separately designed bone-driven lid system; do not restart old VRoid transfer or canthal-pivot methods.

## Reusable next-part production rule
Before moving to eyebrow, hair, ear, accessory, or clothing part, require: canonical source + anchor/coordinate frame + semantic vertex groups + non-destructive modifier/rig contract + deterministic render matrix + numeric/art gates. This reduces rework; no promise of completion until G1–G4 actually pass.

## Claude handoff (optional, narrowly scoped)
Ask Claude to perform an **independent static audit**, not regenerate assets:
1. Compare the exact margin-selection predicates and propose one shared half-edge graph extraction algorithm, with pseudocode and tests for open/closed chains and canthi ordering.
2. Audit `apply_corrective_06.py` for literal `\\n` syntax defects, projection sign and unit conversion, `elm_patch` domain, and candidate-only guard; cite line numbers.
3. Specify 3D arc-length correspondence and collision/occlusion tests, without guessing canonical vertex coordinates.
4. Return a patch suggestion and test matrix only. No edits to canonical files, no bypass flag, no merge.
ChatGPT remains integrator and independently verifies all proposed changes.
