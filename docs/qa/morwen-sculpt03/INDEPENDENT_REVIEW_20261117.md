# Independent review — SCULPT03 local eyelid prototype

Reviewer: separate QA agent, not the geometry author. Review date: 2026-11-17 UTC. Candidate SHA-256: `a04decd5d2b87a86725550fb545b8b118125a07d7c1010f82aaa6aeb54df3353`.

## Evidence and scope

Independently reopened the source and candidate in Blender 4.3.2 with scripts disabled. Ran the existing read-only mesh inventory on each, then an independent bmesh/UV/blink sampling script on the candidate. Read the build script and manifests; inspected actual packed approved design sheet, baseline front, candidate front/profile, isolated open/half/closed blink and both control-wire renders. This is an AI independent review; no human artist or Android device review occurred. Numeric evidence is in `INDEPENDENT_LOCAL_SCREEN.json`.

## Source integrity — limited check PASS

SCULPT02 file SHA matches the required `90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b`. All 57 source control-mesh coordinate/connectivity fingerprints and shape-key displacement summary records match the candidate; exactly two eyelid mesh objects were added. All five packed reference-image hashes match the approved manifest. This protects the checked geometry/references; it does not establish accurate artistic registration or certify every scene/material property unchanged.

## Local topology — limited screen PASS

Each new patch has 48 control vertices, 32 quad faces, two expected 16-edge boundary loops, no wire edges and no unexpected non-boundary nonmanifold edges. At blink 0, 0.5 and 1, each evaluated patch has 576 vertices/512 faces, finite coordinates, zero faces below 1e-12 area and zero backward-facing normals. Left UV island is consistently mirrored relative to right; no within-patch signed-area reversal was detected. These are deliberately open surfaces and local planar study UVs, not a watertight character or production atlas.

The wire images demonstrate new corner-connected control topology and distinct upper/lower arcs. The implemented coordinates/connectivity differ causally from automatic polar-angle sampling or zipper triangulation. The study does not repeat Grab deformation or generate another coarse hair variant. This is a new local technical prototype, not completed manual facial retopology.

## Art findings — G2 FAIL

1. Candidate front visibly shows two raised orbital rings around the old eyes. The old face remains beneath them; there is no continuous skin transition, and eye/glasses relationships remain unresolved. A larger ring opening alone does not create the approved eye identity.
2. Nose, jaw and facial proportions still read as the inherited realistic head. The approved source has softer anime planes and larger expressive eyes. The prototype does not resolve that discrepancy.
3. Hair remains the inherited thick cap/bowl with solid petal-like fringe and a broad uninterrupted profile/back mass. No new rooted layered bob was produced. Its previous G2 FAIL remains in force.
4. Isolated blink images show coherent narrowing, but the closed sample retains a seam/gap. Without eyeballs, face integration and contact/intersection testing, this is a diagnostic morph only. It is not accepted blink animation or a facial rig.
5. The isolated wire and smooth patches are useful intermediate evidence. They support editing and further integration, not final-art acceptance.

## Gates and next work

- G1 **BLOCKED**: source and packed hashes pass; accurate front/profile landmark registration and identity acceptance remain unresolved.
- G2 **FAIL**: inherited character discrepancies plus visibly unintegrated eyelid rings.
- G3 **INCOMPLETE**: local finite/area/boundary/winding screen passes; skin/eyeball collisions, self-intersections, UV atlas, rig and deformation acceptance are not certified.
- G4 **NOT_RUN**: no WebGL/Android/game integration or performance acceptance.

Keep this prototype and all previous failures. Next useful deliverable is an artist-reviewed front/profile face target, followed by integrated orbital/cheek/nose topology with eyeball clearance and closed-blink contact testing. Do not scale/tune floating rings and claim finished facial retopology. Rooted layered hair, full face, clothing/equipment, production materials, rig and animation remain unfinished. No formal adoption, main merge, original replacement, map edit or publication is authorized by this review.
