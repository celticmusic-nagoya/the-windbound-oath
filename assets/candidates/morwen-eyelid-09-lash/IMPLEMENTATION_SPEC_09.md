# MORWEN EYELID-09 — Independent lash architecture / execution contract

Status: DESIGN_ONLY / NOT_ADOPTED / NO_GEOMETRY_BUILT
Base: EYELID-08 disabled candidate at bca7d1d4cfd4b5e8a4f6c03656e148ed8485370c
Scope: new candidate only. No changes to canonical Face, its vertex indices, or its 58 shape keys.

## Evidence / baseline
- EYELID-08 50% contact shell: right 672 vertices/1178 polygons, left 674 vertices/1182 polygons; geometry self/eye/attachment intersections zero.
- Opaque alpha-card samples inside shell: right 45, left 23; 2753 finite samples in total. G3 FAIL.
- Minimum projected normal thickness near corners: right 0.0174 mm, left 0.0229 mm. Do not confuse with 0.6 mm anterior-axis shell offset.
- G1 protected fingerprint PASS, canonical binary comparison BLOCKED; G2 NOT_RUN, G4 NOT_RUN.
- The old constrained PSLG family and Dirichlet harmonic eyelid family are stopped after documented failures. Do not reset attempt counters by renaming or retuning parameters.

## Architectural decision
Build independent lash strips/tufts anchored to the evaluated upper eyelid surface, not by lifting existing alpha-card vertices out of a shell. Preserve original lash cards and EYELID-08 shell as read-only reference; write new objects under a separate M09 candidate collection. No canonical geometry edits.

### A. Attachment data
For each lash root, persist: side (R/L), lid-surface face/triangle ID, barycentric coordinates (u,v,w; sum=1), local surface tangent and anterior normal, normalized arc-length position, source reference ID, and deterministic seed. Reject roots outside the selected upper-lid region. Keep left/right independently authored; do not blindly mirror asymmetric design.

### B. Evaluated geometry
At each sampled lid state, evaluate root position as barycentric interpolation on the *evaluated* lid mesh. Build an orthonormal tangent frame from evaluated triangle and a stable upper-lid tangent. Construct lash roots just outside the contact surface using a measured offset, then sweep strips/tufts with taper and curved direction. Constrain the root region against surface penetration; never rely on finite vertex lifting of existing alpha cards. For motion, compare orientation and root continuity between states; avoid triangle-index instability by retaining fixed candidate topology.

### C. Collision and appearance QA
- Broad phase: BVH/AABB for each evaluated mesh and lash strip.
- Narrow phase: triangle-triangle intersection between opaque lash geometry and closed lid shell, including coplanar overlaps; alpha-aware tests only where transparent cards remain. Finite alpha samples alone do NOT prove continuous collision freedom.
- Check root-to-lid attachment gap and penetration separately from intentional coincident root attachment; define an explicit epsilon and report its units.
- Measure front/rear thickness in local normal direction, especially both canthi; do not mark PASS based solely on Y-axis offset.
- Record eye/face intersections, non-manifold edges, inverted normals, flipped UVs, silhouette discontinuity, and alpha artifacts.
- Render 5 fixed cameras: front, q3L, q3R, left, right; include close-up and game-display-size sheets. Require visual assessment for lash density, outer-corner taper, eyelid shape, and original character identity.

## Staged execution / gates
Stage 0: Verify input SHA-256, source fingerprint, Face vertex count 1972, all 58 shape key names/order/data. If original canonical v5.61 is inaccessible, G1 canonical comparison stays BLOCKED.
Stage 1: Build a SINGLE independent 50% lash candidate from frozen EYELID-08 reference. Existing candidate shell stays disabled; do not enable it for production.
Stage 2: Technical QA at 50%: zero unintended opaque-lash/lid intersections for both eyes, zero self/eye/face intersections, stable root attachment, valid topology and normals, no new backface see-through. Report exact numeric thresholds and failures.
Stage 3: Independent artistic QA from 5 views at close-up and target display size; require explicit human approval of silhouette and eyelash design. CI success is not art PASS.
Stage 4: Only after 50% technical/art PASS, expand to 0/25/75/100% and independent L/R wink, evaluating every intermediate motion sample; finally G4 game/Android QA.
Failure policy: maximum two meaningful attempts per identical root cause/method family; stop, preserve evidence, and redesign if both fail.

## Reference-video acquisition protocol
Search targeted real high-speed blink/wink footage, anatomical eyelid/lash close-ups, high-quality 3D facial rigs, and Blender eyelid/eyelash workflows. Record URL, author, publication/license, exact useful frame or time interval, technique learned, and whether content may be redistributed. External video is a *reference*, not a licensed game asset. Do not claim a video was analyzed unless frames/time intervals were actually inspected.

## Evidence outputs expected from implementation
- Reproducible Blender script + version, source hashes, deterministic seeds, candidate .blend.
- 5-view PNGs and target-size review sheet.
- Machine-readable geometry/penetration/thickness QA JSON with per-eye counts and state names.
- Attempt ledger entries, failure classification, provenance and licensing manifest.
- Final explicit G1/G2/G3/G4 statuses, with NOT_RUN/BLOCKED where appropriate.

## Current status
Branch preparation and this specification: COMPLETE.
Actual new lash geometry, Blender execution, new renderings, art review, animation, G4: NOT_RUN.
No main merge, source overwrite, production enablement, or publication authorized.
