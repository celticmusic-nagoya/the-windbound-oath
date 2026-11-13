# MORWEN-3D-ART-ACCEPTANCE-01 | Independent art QA contract
Status: REVIEW CRITERIA ONLY / NO MODEL APPROVAL. Date: 2026-11-14.

## Canonical hierarchy
1. Approved visual master: `docs/design/MORWEN_V561_CANONICAL_20261108.md` references director-provided `7374.png` (actual JPEG; SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`), binary not yet stored in GitHub. Do not replace it with another similar image.
2. Approved full-body master `assets/companions/morwen/master/morwen-full-body-v3.png` per `docs/lore/MORWEN_CANON_20261108.md`. Verify hash/contents before asset-level comparisons.
3. Layer 0 four-view body reference: `tools/blender/production_mesh_08/references/{7809,7807,7810,7808}.png`, distinct from finished-costume sheet.
4. `docs/art/MORWEN_3D_TARGET_SHEET_20261113.md`: director-confirmed higher-quality PNG `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png`, SHA-256 `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957` (GitHub Actions #43459999519 PASS). The older JPEG is superseded and must not be used. Treat this PNG as the **3D production target**, not an unapproved replacement for canonical v5.61. Where images disagree, block and request director decision.

## Part-specific acceptance checks
| Part | G1/G2 visual criteria | Evidence required |
| --- | --- | --- |
| Face | soft oval face, violet eyes, small nose/mouth, gold-rim glasses; facial proportions consistent in front and profile; 18-year-old character | head front/right/left plus 3/4 comparison, explicit landmarks and no geometry gaps |
| Hair | violet short layered bob, bangs and side locks, believable volumetric strands, rear silhouette consistent | 4 views, hair-only and shaded renders |
| Hat | asymmetric broad purple brim and folded pointed crown; purple flower, ribbon, suspended gem, gold trim; side-specific placements must not be mirrored | four views, exploded parts/material IDs |
| Uniform | purple/black/gold academy uniform, shoulder open-book crest, gold embroidery, pleated skirt, layered cape; preserve approved asymmetric ornament positions | four views, close-ups, material IDs |
| Props | magic book, leather satchel and strap, potion holder/vials, chain, belt, earrings | four views, individual component proof |
| Legs/boots | **knee-high socks, not tights**, approved lace-up boots, believable skirt-to-leg overlap | full-body 4 views, knee/ankle detail |
| Materials | readable differences in velvet/cloth, leather, gold, hair, skin and glass; no z-fighting, inverted normals, black artifacts | neutral-clay, material-ID and final-lit renders |

## Non-negotiable production QA
- Same world scale, orthographic camera calibration, root/foot anchor, consistent lighting and transparent background for front/right/back/left.
- Compare final display at 32, 40 and 48 px character height where applicable; never assume that a detailed high-resolution render will remain legible.
- Deformation: neutral, head rotation, walking extremes; no face holes, cloth clipping, hair/hat penetration, broken ornaments.
- No mirrored asymmetric ornaments; no missing accessories. Preserve source PNG hashes, Blender version, seed, build script and artifact digest.
- Geometry source, UV, material, rig, draw-call/triangle budget and Android runtime remain independently gated.

## G2 acceptance rubric
Each part receives PASS / FAIL / BLOCKED with side-by-side evidence. PASS requires recognizable canonical silhouette in all relevant views, correct key colors and asymmetry, no obvious material/mesh artifacts at production and game size. Numeric landmark tolerances cannot be declared before calibrated references and approved measurements exist. Do not score aesthetic quality as a proxy for objective matching.

## Current verdict
- Run #43453993945: Blender 4-view isolated skin mesh render SUCCESS, but 588-vertex island renders show holes and severe shading artifacts; **G2 FAIL**, diagnostic visualization integrity FAIL. This is not an approved head or valid basis for face-fitting.
- Current candidate hair, uniform and face are NOT_APPROVED for Morwen.
- Claude may investigate components, normals, material/alpha and build diagnostic renders on separate branch; ChatGPT handles independent visual QA. Avoid parallel edits to the same pipeline files.
- G1 PNG binary integrity PASS, canonical design comparison PENDING; G2 FAIL for existing candidate; G3 pipeline PASS, diagnostic quality FAIL; G4 NOT_RUN.

## Director decision needed only after evidence
Approve/reject a complete reconstructed head and costume; any proposed change to canonical silhouette or asymmetric details requires explicit director approval. No source overwrite, main merge or publication.
