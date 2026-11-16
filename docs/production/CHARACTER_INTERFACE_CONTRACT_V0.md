# CHARACTER-INTERFACE-01 — Shared immutable contract (v0, pending canon)

Status: DRAFT / UNLOCKED / NOT_FOR_MODELING. Source: PR #332 production and handoff specifications; main AGENTS.md; current main canon references. All unspecified numeric values are null, never guessed.

## Scope
Target Morwen first. Fiona and Aidan require independent per-character manifests. Interface changes require a reviewed interface PR; no producer silently changes the contract.

## Verified sources
- Main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md checked 2026-11-16.
- Morwen design master: user attachment 7374.png, actual JPEG 1536x1024, SHA-256 47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638. Binary NOT in public GitHub; visual G1 BLOCKED.
- docs/design/MORWEN_V561_CANONICAL_20261108.md and data/morwen-design-canonical.json: DESIGN_REFERENCE_APPROVED, production sprite NOT APPROVED.
- Private lore main CANON_STATUS.md and CANON_ADDENDUM.md accessible; full private bible and latest image binary still require exact verification before lock.
- Current eyelid/lash experiment: Draft PR #327; 09P surface collision FAIL; 09Q diagnosis pending. Do not alter its assets or reset its retry ledger.

## Required interface values
| Field | Status | Value or action |
|---|---|---|
| character_id | CONFIRMED | morwen |
| design reference SHA | CONFIRMED_METADATA_ONLY | 47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638 |
| head/body ratio | DIRECTOR_APPROVED_TARGET | 7.5–8.0 heads for new anime-style 3D character models; exact per-character ratio must be matched to the accepted Layer 0 source, not invented |
| world unit and origin | BLOCKED | derive from approved Layer 0 blend, verify actual object transforms |
| coordinate axes / 4 directions | BLOCKED | derive from source rig and game camera, no axis guessing |
| camera / framing | BLOCKED | derive from current field renderer |
| neutral pose | BLOCKED | inspect approved rig/Layer 0 |
| neck seam coordinates | BLOCKED | measure same coordinate frame on head and torso |
| shoulder / waist seams | BLOCKED | measure approved Layer 0 |
| rig bone names / bind transforms | BLOCKED | read actual rig and check parent hierarchy |
| face controls | BLOCKED | inspect current approved controls |
| UV and material slot IDs | BLOCKED | inventory approved Blender data |
| costume layer and occlusion masks | PARTIAL | visual inventory documented; exact mask IDs unverified |
| equipment slot IDs | BLOCKED | inspect existing modular sprite and headgear specifications |
| display dimensions | PROVISIONAL | native 48px and 96px previews required by PR #332; also verify actual 32/40/48px game sizes |
| full-body alpha export | REQUIRED | PNG RGBA with measured alpha, not checkerboard pixels |
| Blender version | VERIFY_PER_JOB | pin and log exact runtime version |
| deterministic seed | REQUIRED | record explicit seed or state no randomness |
| reference license | REQUIRED | document origin and rights, no unknown external asset insertion |

## Contract lock gate
LOCKED only after every BLOCKED field needed by FACE/BODY/COSTUME is measured from the same accepted source and reviewed. An unverified number must not become an interface default. Until then, branches may create source inventories, manifests, tests and designs but NOT claim integrated compatible models.

## G1–G4
G1 source-image/canon comparison BLOCKED; G2 independent artistic review NOT_RUN; G3 source/mesh/interface technical checks NOT_RUN; G4 full-character/game/Android NOT_RUN. GitHub CI PASS cannot certify G2/G4.

## Isolation
FACE owns head/face/hair/expression candidate collections; BODY owns torso/limbs/rig candidate collections; COSTUME owns clothes/accessories/occlusion candidate collections. INTEGRATION consumes frozen reviewed outputs only. Each branch writes assets/candidates/<task_id>/<candidate_id>, tools/character_blender/, docs/qa/. No canonical overwrite, main merge, publication or destructive deletion.

## Director-approved proportion and style override — 2026-11-16
- New 3D character production uses **approximately 7.5–8 heads**, with high-quality anime-style modeling informed by Genshin Impact and Neverness to Everness (NTE). This replaces the 2.8-head target **for new 3D character models and their future in-game presentation**.
- Preserve the exact approved character identity, face, asymmetry, costume, equipment and Layer 0. Visual references are style/technique inspiration only; do not copy third-party character assets or designs.
- Legacy 2D field sprites, their sizes, animations and code remain untouched pending a separate approved migration. The earlier 2.8-head specifications are historical/legacy compatibility references, not the new 3D production target.
- Design the new character at production-quality 3D proportions; validate silhouette and face at actual future gameplay camera and resolution. 48px/96px legacy previews are diagnostic only and do not define the new 3D character's proportion.
- Target is a range, not proof of measured canon geometry. Exact height, head length, neck seam, shoulder and hip positions, bone names and axes remain BLOCKED until verified from accepted Layer 0 and rig.
- This later explicit director decision supersedes conflicting 2.8-head statements in the character work packages and the PR #332 draft **for new 3D modeling only**.

## Source audit 2026-11-16 — critical conflict
- docs/design/MORWEN_LAYER0_REFERENCE_REGISTRY.json (on PR #326 branch) records Layer 0 sheet SHA 7e122ceb205e502aad49dfa32ac463818e30a3da4d4bd43951f9263bcb08a150, dimensions 1536x1024, approximate 163 cm and 7.5 heads; these are **unverified source metadata**, not the field sprite's 2.8-head target.
- tools/blender/production_mesh_08/layer0_reference_manifest.json lists four source panels 7809/7807/7810/7808 with hashes, but explicitly says their image bytes are not in GitHub.
- The reference registry specifies character-left +X, right -X; docs/design/MORWEN_LAYER0_PRODUCTION_GATE.md states local +X is character-right. **AXIS_CONFLICT: BLOCKED** until checked against the accepted image, actual rig, and rendering transforms. Neither statement is silently promoted.
- Existing CONTACT_CAGE_DISABLED_08.blend is a *candidate diagnostic*, not a verified accepted Layer 0 master. Its mesh transforms can be measured for a provisional geometry interface, not promoted to canonical scale or seam.
- docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json labels pixel landmarks approximate and not art-approved; barefoot and booted heights must not be equated.
- The face/body/costume branches remain preproduction; no independently running Claude or Codex session was launched.

## Executed Blender candidate inventory — GitHub Actions run 43811035214
- Job SUCCESS, artifact 14200312401, `PR326_CANDIDATE_INVENTORY.json`; source SHA 9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4 verified by script. Artifact inspected independently.
- Blender 5.3.0, METRIC scale_length 1.0; 16 scene objects, one armature with 83 bones.
- `Body` 7,797 vertices, world bbox min (-0.69174314,-0.15041634,-0.0001845), max (0.69225442,0.13823646,1.59763277) meters.
- `Face` 1,972 vertices, world bbox min (-0.10798285,-0.04119926,1.35438931), max (0.10849377,0.10665022,1.58652210) meters.
- Rig includes `Root`, `J_Bip_C_Hips`, `J_Bip_C_Spine`, `J_Bip_C_Chest`, `J_Bip_C_UpperChest`, `J_Bip_C_Neck`, `J_Bip_C_Head`, `J_Adj_L_FaceEye`, `J_Adj_R_FaceEye` and left/right limbs, fingers, feet, skirt and secondary bones. Full bone hierarchy and bind matrices are in artifact, NOT duplicated in this contract.
- These are **candidate observations**, not approved seam or anatomical measurements. The candidate includes experimental eye and lid meshes and an unrelated Icosphere; do not derive approved height, head ratio or full production assembly from all object bounds.
- Head/body interface alignment, axis handedness, approved reference match and game-camera G4 remain BLOCKED/NOT_RUN.

## Verified bone-review run — 2026-11-16
- GitHub Actions run 43812208625: **SUCCESS**, artifact 14201031871; downloaded and inspected both PR326_BONE_REVIEW.json and PR326_CANDIDATE_INVENTORY.json.
- Bone-review schema TWO_CHARACTER_INTERFACE_BONE_REVIEW_V1; status CANDIDATE_DIAGNOSTIC_ONLY; problems=[]; 83 bones.
- Root -> Hips -> Spine -> Chest -> UpperChest -> Neck -> Head parent links all verified. Neck tail local (0.00025548,-0.01727151,1.38815856), Head root local (0.00025545,-0.00796455,1.38756120). Euclidean distance 0.009326111 m; this is **not** a mesh gap.
- Face mesh bbox height 0.23213279 m, Body mesh bbox height 1.59781727 m; **do not calculate 7.5–8 head compliance from these**, because Face mesh bounding box is not verified anatomical head length.
- Blender scene METRIC, scale_length 1.0; candidate read-only and hash-verified.
- G1 BLOCKED (official reference image bytes unavailable and axis conflict), G2 NOT_RUN, G3 PARTIAL_MEASUREMENT_ONLY, G4 NOT_RUN.
- Next non-destructive QA: evaluate neck skin seam, bone weights, material and UV properties, source-image camera handedness. Do not freeze interface until source and art review agree.

## Verified candidate surface audit — GitHub Actions run 43822625160
- Run SUCCESS, artifact 14205705177; downloaded and independently inspected `PR326_SURFACE_AUDIT.json`, `PR326_BONE_REVIEW.json`, `PR326_CANDIDATE_INVENTORY.json`.
- Body: 7,797 vertices, 11,646 polygons, 1 active UVMap, 6 node-based materials, Armature modifier, 0 unweighted vertices, 0 vertices with >4 influences, 0 unknown bone groups, 3,594 boundary edges, 0 edges with >2 adjacent polygons.
- Face: 1,972 vertices, 2,772 polygons, 1 active UVMap, 9 node-based materials, Armature modifier, 0 unweighted vertices, 0 vertices with >4 influences, 0 unknown bone groups, 756 boundary edges, 0 edges with >2 adjacent polygons.
- The script's `nonmanifold_edges` counts only edges with >2 adjacent faces; **boundary edges themselves are also non-manifold in Blender's broader topology terminology**. Thus 0 is NOT proof of watertight or manifold meshes. Mesh segmentation, loose edges, inverted normals, skin seam and material appearance remain unverified.
- Existing candidate contains both dithered and blended surface render methods, but material alpha appearance, textures and export compatibility are not evaluated.
- Candidate-only basic weight coverage PASS; **G3 PARTIAL**, not full technical acceptance. G1 BLOCKED, G2 NOT_RUN, G4 NOT_RUN. Approved 7.5–8-head model proportions not yet measured.

## Executed boundary spatial audit — 2026-11-16
- GitHub Actions run 43823804372: SUCCESS; artifact 14205502586 downloaded and `PR326_BOUNDARY_REGIONS.json` inspected.
- Body: 3,594 boundary edges, **181 connected boundary components**. Largest component 194 edges, world bbox min (-0.152377,-0.070535,0.817992), max (0.152887,0.079972,1.410416) m; next 160 edges, bbox (-0.157619,-0.106483,0.889923) to (0.158130,0.134552,1.335301) m.
- Face: 756 boundary edges, **33 connected boundary components**. Largest 74 edges / 73 vertices (one degree-4 vertex), bbox (-0.012910,0.058429,1.382223) to (0.013421,0.088985,1.399932) m.
- Components with vertex degree >2 are not simple closed loops. Neither boundaries nor disconnected regions prove defects without canonical part classification.
- Important: the Body's two largest boundary-component bounding boxes span much of the torso and cannot be labeled 'neck seam' without explicit approved seam markers. Do not infer skin continuity or 7.5–8-head compliance from this audit.
- G1 BLOCKED (source image and handedness); G2 NOT_RUN; G3 PARTIAL; G4 NOT_RUN. Next: read-only Body–Face closest-boundary-distance distribution, restrict to anatomically reviewed neck region, verify against 4-view canon, then render visual seam checks.
