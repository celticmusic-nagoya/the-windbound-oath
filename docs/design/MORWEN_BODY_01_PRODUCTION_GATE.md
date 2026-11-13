# MORWEN-BODY-01 | canonical base-mesh gate

Status: SPEC READY; FORMAL BODY NOT YET GENERATED OR ART-APPROVED.
Scope: Morwen only. Do not alter official art, existing character sprites, or main.

## Canonical sources
- Front full-body: `assets/companions/morwen/master/morwen-full-body-v3.png`.
- Three approved views: `docs/design/MORWEN_OFFICIAL_3V_REGISTRATION_20261109.md`.
- Approved side/back PNG binaries are not yet confirmed in GitHub. Treat those angles as **BLOCKED** until source hashes are verified.
- Do not infer unseen clothing, accessories, or silhouette details from a primitive candidate.

## Coordinate contract
- Blender Z up, character front -Y, character left +X = .L, character right -X = .R.
- Root at floor contact. Rest pose shared with future humanoid rigs.
- Head height, shoulders, pelvis, knees, ankles and sole height must be measured from the approved reference before freezing geometry.
- Use a single normalized coordinate system; avoid object-scale transforms on deforming mesh.

## Production stages
1. Reference registration: validate the three view PNGs against SHA-256 in the design tracking document.
2. Proportion sheet: measure ratios from front and registered side/back images; do not invent numeric proportions.
3. Reusable base mesh selection: confirm redistribution rights, topology, symmetric neutral pose, and deformation-ready joints. Keep license/source manifest.
4. Whole-body primary forms: match front, sides, back silhouettes. No clothing detail polish until proportions pass.
5. Face/hair, then garments and accessories as separate editable modules. Protect canonical asymmetric details.
6. Shared rig fit, weight QA, walk/idle tests, four-view sprite output.

## Stage gates
- G0 references complete and verified: NOT_RUN / missing three view binaries.
- G1 neutral full-body silhouette from four views: NOT_RUN.
- G2 joint bending and topology: NOT_RUN.
- G3 clothing/hair consistency with official art: NOT_RUN.
- G4 rig, animation, Android/game view: NOT_RUN.

## Reuse policy
- `mvp_blockout_01` is technical proof only, not the base of formal Morwen.
- Keep `TWO_MasterRig_v1` as a candidate; apply only after G1.
- No automatic art PASS based on file presence or successful render.
