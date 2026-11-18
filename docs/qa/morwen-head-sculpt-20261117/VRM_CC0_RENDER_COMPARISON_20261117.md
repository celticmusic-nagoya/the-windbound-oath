# Legacy VRoid vs current CC0 head — render evidence comparison (2026-11-17)

## Actual inspected source files
- PR #316 Actions 43575126139, Artifact 14106227834: `MORWEN_ELM_04_CANDIDATE.blend` (8,627,692 bytes; SHA-256 prefix `6c5a9919fd6733a0`), `renders/cand_neutral/front_toon_face.png`, `renders/cand_neutral/q3L_toon_face.png`.
- PR #318 Actions 43587116653, Artifact 14111116241: `MORWEN_EYELID_05_CANDIDATE.blend` (8,640,? bytes; SHA-256 prefix `db9576531f7da777`), `renders/cand_neutral/front_toon_face.png`.
- PR #399 Actions 44064066566, Artifact 14319881962: `morwen_head_study_UNAPPROVED.blend` (15,930,885 bytes; SHA-256 `4e818c24d9d05258bd0c4f5a1cc6116826807a234aa7819f65fc49cc01f307d7`), `front.png`, `three_quarter.png`.
- A five-panel diagnostic sheet was composed in the inspection environment from the five original PNGs. It was **not** committed to the repository and is not a new Blender render.

## Visual observation
- Legacy #316/#318 face is stylized: larger iris-to-face ratio, simplified nose and mouth, tapered jaw. This is useful for art-direction reference, but the hairstyle and outfit shown in these renders are NOT Morwen canon.
- Current #399 face is realistic: smaller eyes and more realistic nose/mouth/chin. Hair reads as evenly spaced rigid wedge bangs and a smooth helmet-like shell; independent G2 FAIL stands.
- The legacy eye appearance may inform a redesign, but copying its facial geometry or shape keys without compatibility testing is **not approved**.
- Cameras, crops, lighting and materials differ. This is a qualitative diagnostic, not a calibrated geometric comparison. Do not infer dimensional or topology compatibility.

## Concrete production decision
Prioritize **a new anime-stylized face art direction grounded in Morwen's official design** while retaining the current 7.75-head measurement framework. Use #316's eyes and expression setup as reference or transfer candidate only after checking actual .blend topology, armature, shape key names, licensing and UV. Do not reuse #318's failed animated eyelid deformation or the old procedural face/hair methods. The exact .blend bytes have been recovered, but the Blender runtime was not available for opening and interrogating them in this inspection environment.

## Gate status
- G1 BLOCKED: no calibrated canonical image overlay
- G2 FAIL: existing #399 head; legacy render is REFERENCE_ONLY
- G3 PARTIAL: source .blend presence and render extraction verified; topology/rig/transfer NOT_RUN
- G4 NOT_RUN: no game or Android integration
- No merge, deletion, canonical overwrite or publication.
