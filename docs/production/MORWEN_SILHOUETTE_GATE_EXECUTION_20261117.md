# Morwen silhouette gate — verified execution and next dependency (2026-11-17)

## Executed evidence
- Canonical reference audit workflow: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44031362211 — SUCCESS.
- Evidence artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44031362211/artifacts/14305706165.
- Five official reference images verified for SHA-256 and expected dimensions; Layer0 alpha>=128 bounding boxes measured. **This does not establish final full-body anatomy or costume silhouette**.
- Previous continuous hair-shell run 44027858379 succeeded technically but failed independent G2 art QA; do not repeat hair detailing before body G2.

## Existing work reused, not duplicated
- `MORWEN_BASEMESH_DIMENSION_COMPARISON_20261117.md`: existing Blender Studio CC0 female basemesh candidates measured; stylized X/Z 0.4458, realistic X/Z 0.5138. These are overall bounding boxes, not anatomical landmark measurements.
- `MORWEN_FULLBODY_BASEMESH_SELECTION_20261116.md`: 7.5–8 head ratio and reviewer-confirmed landmarks contract.
- `MORWEN_CANONICAL_VS_GENERATED_TURNAROUND_QA_20261117.md`: already documented failure of prior generated turnaround (wrong flower, crest, skirt, garter, bag, cape, stockings).
- `MORWEN_HIGH_QUALITY_3D_RESTART_20261117.md`: basemesh license and production sequence already specified.
- Do not create another redundant proportion spec, generic silhouette script, or placeholder render.

## Decision / blocking gate
**Next work must operate on actual Blender basemesh geometry**, not alpha bounds. Existing 1.4.1 CC0 candidate is not yet approved as Morwen. Need (1) select real stylized/realistic mesh by topology and silhouette, (2) measure anatomical skull crown/chin/sole and major landmarks, (3) compare four calibrated full-body neutral renders against the canonical design sheet and Layer0 under documented view transforms, (4) create a new editable proportion candidate only after evidence. If reviewer-confirmed anatomical landmarks cannot be established, record G1 BLOCKED and do not infer them.

G0 source SHA PASS; G1 model/canonical correspondence BLOCKED; G2 finished silhouette NOT_RUN; G3 full-body topology/rig NOT_RUN; G4 NOT_RUN. No canonical files changed, no main merge, no release.
