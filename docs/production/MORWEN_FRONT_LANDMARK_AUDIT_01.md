# MORWEN FRONT LANDMARK AUDIT 01 — 2026-11-16
Status: MEASUREMENT_PREPARATION_COMPLETE / ARTIST_LANDMARK_REVIEW_REQUIRED / FRONT GENERATION BLOCKED

## Source
Canonical Layer 0 front: `assets/canonical/morwen/2026-11-16/LAYER0_FRONT.png`, SHA256 `b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed`, 384×1024 RGBA. The supplied original was reopened for this audit; pixel-row extents were sampled at alpha >128. These are **silhouette measurements**, not anatomical landmark identifications.

## Source landmark ledger (image coordinates, y down)
| Feature | y px | Evidence | Confidence |
|---|---:|---|---|
| Hair crown/top | 17 | Existing proportion JSON, image inspected | approximate |
| Chin | 178 ±4 | Prior visual estimate, not independently calibrated | LOW |
| Narrowest waist | 353 | Existing proportion JSON, not newly hand-annotated | LOW |
| Crotch | 500 | Existing proportion JSON, not newly hand-annotated | LOW |
| Stocking top | 553 | Existing proportion JSON, not newly hand-annotated | LOW |
| Floor/feet | 1003 | Existing proportion JSON, image sampled | approximate |
| Shoulder joint center | null | Hair/arm/torso overlap; requires manual annotation | BLOCKED |
| Bust apex | null | Garment/body contour cannot reliably establish landmark | BLOCKED |
| Knee joint centers | null | No skeletal landmark in raster; requires manual annotation | BLOCKED |
| Ankle joint centers | null | Sock/foot silhouette alone insufficient | BLOCKED |
| Elbow/wrist joint centers | null | Requires independent hand annotation | BLOCKED |

### Silhouette row samples (alpha >128)
`y=17 x=198..229; y=175 x=125..298; y=350 x=111..317; y=500 x=63..364; y=550 x=59..367; y=750 x=140..283; y=950 x=162..261; y=1003 x=182..244`.
These include hands, hair and accessories where present; **do not** interpret the extrema as shoulder/waist/knee widths.

## Geometry/QA decision
- The previous proportion design JSON describes a **head-only scaling rule**; that rule is superseded for production by director-approved holistic 7.75-head redesign. Do not overwrite the historical JSON; store the new calibrated anatomy separately.
- Absolute stature in centimeters remains unapproved. Do not promote the generated concept-sheet `155–158cm` label as fact.
- Orthographic front candidate requires confirmed joint landmarks and a separately recorded front silhouette; **do not generate another composite sheet**.
- The current front-only preflight spec sets `landmarks_reviewed_by_artist=false` intentionally. Its validator should fail closed until an actual annotation and review exists. Never change the flag merely to get PASS.
- Anatomical right garter is screen-left in front view; visible in rear on screen-right.
- Image-generation of a new front view is NOT_RUN in this audit; G1/G2 NOT_RUN for new candidate; G3 source silhouette sampling PARTIAL; G4 NOT_RUN.

## Method-family circuit breaker
- `unconstrained-composite-image-generation`: failed twice (V1.0 and V1.1) and **STOPPED**.
- `measured-single-view-orthographic-construction`: new method, zero executed image-generation attempts; requires independent landmark review before execution.
- A new prompt, agent, model or renamed file does not reset the exhausted method family.

## Next executable action
Use the canonical Layer 0 front in a human-reviewable landmark annotation overlay, manually label shoulder, bust, elbow, wrist, hip/crotch, knees and ankles, and approve the geometric construction spec. Then run `python tools/character_blender/validate_morwen_front_only.py docs/production/MORWEN_FRONT_ONLY_01_SPEC.json` and expect FAIL until all source landmarks are reviewed. Only after PASS may a single full-body front candidate be created.
