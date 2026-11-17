# Morwen legacy VRoid reuse triage — 2026-11-17

Status: DOCUMENTED_EVIDENCE_ONLY. No mesh transfer, Blender execution, or new artistic approval performed.

## Evidence inspected
- PR #306: experimental cheek/jaw refinement on copied complete VRoid Face+Body; four-view Cycles CI. Source unchanged; G2 requires independent visual QA.
- PR #316: procedural violet eye candidate and eyelash/eyeliner card rebind; 56 shape keys retained, Blink technical tests, 0 opaque card burial in tested states, unresolved transparent-card intersections, mouth deformation defects. Annulus/zipper lid and mouth method failed twice and is stopped. 16 additional shape keys unreviewed.
- PR #318: canthus-anchored quad eyelid strips statically matched Layer0 dimensions, but both key-transfer and analytic bone-like closure families failed deformation tests. G3 FAIL; not reusable as an approved animated lid.
- PR #339: legacy VRoid beta CC0 base_female baseline ~6.57 silhouette heads, no Morwen-specific hair, hat, clothing or accessories. Not suitable as the final approved model. Reuse classification from previous audit: VRoid as expression/rig reference, not complete body replacement.
- PR #399: current Blender Studio CC0 head candidate measured 7.749997 anatomical heads, technical screen PASS, G2 independent FAIL for realistic face and regular shell hair. Existing candidate must remain preserved.

## Reuse decision matrix
| Element | Status | Required before integration |
| --- | --- | --- |
| VRoid face mesh and topology | REFERENCE_ONLY | Obtain exact source .blend/VRM and SHA; compare vertex loops, scale, license, topology and actual sculptability with current CC0 head |
| VRoid expression shape-key names/logic (56 reported) | REFERENCE_ONLY | Export names, pose states and evaluation images; determine remapping strategy, check facial rig, preserve approved asymmetry |
| PR #316 eye/iris material | TECHNIQUE_CANDIDATE | Verify provenance, evaluate against official purple eye appearance and new eye socket; do not copy geometry blindly |
| PR #316 eyelash/eyeliner cards | TECHNIQUE_CANDIDATE | Retest intersections, opacity and all shape keys on current mesh |
| PR #318 static lid quad design | REFERENCE_ONLY | May guide topology; original animated solution G3 FAIL, do not promote |
| Old annulus/zipper lids/mouth and old eyelid deformation methods | REJECTED_METHOD | No same-family retries |
| VRoid full body and old 6.57-head silhouette | REFERENCE_ONLY | Not approved replacement for 7.75-head current candidate |
| Old Morwen-specific hair, hat and costume | NOT_FOUND_IN_PR339_BASELINE | Must not claim they exist |

## Recommended next non-destructive execution
1. Fetch actual PR #306/#316/#318 artifacts and identify precise face/eye/rig source files with SHA and licenses.
2. In a **separate comparison stage**, render old VRoid face and current CC0 head using matched orthographic cameras and neutral lighting; produce front/side/3-4 contact sheet at 64px and 128px.
3. Extract mesh topology/shape key inventory and determine whether **data or method** can transfer. Avoid mesh merging until topology/scale/rig compatibility demonstrated.
4. Choose facial art direction using the official five-image canonical set; never equate VRoid style with Morwen's official identity.
5. New art-directed sculpt/retopo only after comparison. No procedural reattempt of failed hair or eyelid families.

G1: BLOCKED for model-to-canon fit; G2: FAIL for existing #399 candidate, reuse art QA NOT_RUN; G3: PARTIAL evidence from past PRs only, compatibility NOT_RUN; G4: NOT_RUN.
No main merge, source overwrite, deletion or publication.
