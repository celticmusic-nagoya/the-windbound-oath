# MORWEN-BODY-01 | canonical base-mesh gate

Status: SPEC READY; FORMAL BODY NOT YET GENERATED OR ART-APPROVED.
Scope: Morwen only. Do not alter official art, existing character sprites, or main.

## Latest Layer 0 canonical reference (director-selected, 2026-11-12)
- Primary: `モルウェン共通素体キャラクターシート.png` (ChatGPT file Library; four-view sheet). This supersedes the earlier assumption that the clothing turnaround is the base-body reference.
- Visible reference facts: approximately 163 cm (including boots in note), ~7.5 heads tall, front/right/left/back, foot-contact origin (0,0), front view and symmetric neutral pose. Reference sheet contains palette and anchor landmarks.
- Keep the exact image bytes as canonical input. Library image is **not yet committed to GitHub**; do not invent a repo path or hash. Confirm source hash when transferring.
- Layer 0 body silhouette is the shape source; Layers 1-3 are clothing/accessories and must not be baked into the shared body.

## Earlier references (secondary)
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
1. Reference registration: preserve the latest Layer 0 four-view sheet unchanged and register its SHA-256. Earlier clothing side/back sources are secondary and must not block Layer 0 proportions.
2. Proportion sheet: measure ratios from front and registered side/back images; do not invent numeric proportions.
3. Reusable base mesh selection: confirm redistribution rights, topology, symmetric neutral pose, and deformation-ready joints. Keep license/source manifest.
4. Whole-body primary forms: match front, sides, back silhouettes. No clothing detail polish until proportions pass.
5. Face/hair, then garments and accessories as separate editable modules. Protect canonical asymmetric details.
6. Shared rig fit, weight QA, walk/idle tests, four-view sprite output.

## Stage gates
- G0 latest Layer 0 four-view identified and visually inspected: PASS; GitHub binary registration/hash verification: NOT_RUN.
- G1 neutral full-body silhouette from four views: NOT_RUN.
- G2 joint bending and topology: NOT_RUN.
- G3 clothing/hair consistency with official art: NOT_RUN.
- G4 rig, animation, Android/game view: NOT_RUN.

## Reuse policy
- `mvp_blockout_01` is technical proof only, not the base of formal Morwen.
- Keep `TWO_MasterRig_v1` as a candidate; apply only after G1.
- No automatic art PASS based on file presence or successful render.
