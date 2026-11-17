# Morwen anatomical landmark review — evidence and stop conditions

Status: LANDMARK REVIEW PREPARATION; no landmark measurements approved.

## Verified implementation
- Synthetic regression tests: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43981188844 (SUCCESS).
- Calculator: `tools/character_blender/measure_basemesh_landmarks.py`.
- Review template: `docs/production/MORWEN_BASEMESH_LANDMARKS_TEMPLATE.json`.
- Neutral orthographic renders: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43974285450 (8 PNGs).
- Mesh sources: Blender Studio Human Base Meshes v1.4.1 CC0, objects `GEO-body_female_stylized` and `GEO-body_female_realistic`.

## Measurement protocol
1. Keep all reference images and source .blend immutable. Open source in isolated Blender workspace; record source SHA and Blender version.
2. Inspect actual mesh topology in edit mode at orthographic front, side and rear views, with consistent world Z coordinates and no pose deformation. Check world transforms and whether meshes share an origin.
3. Reviewer identifies head-top (skull excluding hair), chin, anatomical shoulder/acromion, waist, hip, crotch, knee, ankle, sole. The knee/ankle/shoulder require a side and explicit left/right decision if asymmetric. **Do not use global mesh min/max as substitutes for anatomical landmarks.**
4. Save each marked vertex or anatomical surface point's world coordinates plus vertex index/barycentric evidence and screenshots. A Z-only entry without corresponding reviewer evidence is not sufficient for G1/G2 approval.
5. Review the points and record reviewer name/date/method before setting `reviewer_confirmed=true` in the template. Unreviewed coordinates stay `null` and BLOCKED.
6. Run `python tools/character_blender/measure_basemesh_landmarks.py docs/production/MORWEN_BASEMESH_LANDMARKS_TEMPLATE.json --output qa_output/morwen_landmarks/measurements.json`. A successful process with BLOCKED values is not a measurement PASS.
7. Compare both meshes against target 7.5–8 heads (design target 7.75), then confirm with the five canonical images. Treat source image 6.1-head stylization as visual reference, not final proportions. Do not change the canonical files.
8. Independent G1/G2 review before production selection. Game G4 remains NOT_RUN.

## Current gate state
- Calculator synthetic tests: PASS.
- Actual anatomical landmark identification: NOT_RUN.
- Both candidate head-counts: BLOCKED.
- Model canonical G1: BLOCKED; G2: NOT_RUN; G3: diagnostic render PASS only; G4: NOT_RUN.
- No production mesh or approved 3D turnaround created. No main merge or publication.

## Stop condition
Do not produce synthetic or guessed landmark measurements merely to unblock the next stage. If a qualified reviewer or verifiable Blender annotations are unavailable, retain BLOCKED and proceed only with independent, non-destructive work.
