# Morwen Layer 0 four-view silhouette measurement — 2026-11-20

Status: **SOURCE HASH PASS / ALPHA SILHOUETTE MEASURED / REFERENCE BLUEPRINT PARTIAL / NOT ART ADOPTION**.

## Evidence and provenance
- Existing owner: Draft PR #427, branch `feature/morwen-artdirected-sculpt-20261119`.
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515
- Evidence artifact (14-day retention): https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515/artifacts/14602858760
- Tested HEAD: `6e275fe54fdd98e7b10016454ccbf44be59a36f6`.
- Original source: PR #419 branch `feature/morwen-rebuild-01`, `tools/blender/production_mesh_08/references/`.
- Code: `tools/morwen_authored_sculpt/extract_layer0_silhouette_landmarks.py`.
- Outputs in artifact: four exact reference PNG files; `reference_verification.json`; `reference_silhouette_landmarks.json`; `four_view_contact_sheet.png`.
- Exact original source SHA256 and 384x1024 dimensions verified for all four views. See `docs/production/morwen_layer0_recovered_source_inventory_20261118.json` for provenance.

## Observed measurements (pixels only; alpha >=128)
The bounding rectangles are min_x, min_y, max_x, max_y; widths/heights are inclusive. These measure **visible artwork** (which may include costume/hair/equipment), not body anatomy or meters.

| View | File | Alpha bbox xyxy | Visible height | Bbox width |
|---|---|---|---:|---:|
| Front | 7809.png | (54, 17, 372, 1003) | 987 | 319 |
| Right | 7807.png | (93, 16, 313, 1002) | 987 | 221 |
| Back | 7810.png | (14, 16, 330, 1001) | 986 | 317 |
| Left | 7808.png | (63, 16, 280, 1002) | 987 | 218 |

Measured alpha silhouette widths at relative visible-height scanlines, in pixels:

| Fraction top-to-bottom | Front | Right | Back | Left |
|---:|---:|---:|---:|---:|
| 0.00 | 32 | 29 | 26 | 31 |
| 0.05 | 137 | 161 | 140 | 163 |
| 0.10 | 170 | 170 | 173 | 172 |
| 0.15 | 187 | 165 | 193 | 163 |
| 0.20 | 153 | 67 | 151 | 68 |
| 0.25 | 188 | 142 | 192 | 142 |
| 0.30 | 197 | 116 | 200 | 116 |
| 0.40 | 252 | 119 | 252 | 123 |
| 0.50 | 308 | 127 | 306 | 131 |
| 0.60 | 164 | 94 | 169 | 94 |
| 0.70 | 124 | 73 | 127 | 74 |
| 0.80 | 137 | 71 | 143 | 73 |
| 0.90 | 96 | 43 | 101 | 43 |
| 0.95 | 102 | 78 | 106 | 79 |
| 1.00 | 63 | 25 | 78 | 20 |

## Interpretation and next production use
- Verified: image bytes match expected SHA-256, dimensions, silhouette measurements and the GitHub Actions runtime output.
- **Not inferred:** true anatomical landmarks, head/body ratio, camera projection, real-world scale, mesh topology, facial geometry, VRoid-fit, or G2 artistic acceptance.
- Image-left vs character-left, pose shifts and asymmetrical costume may affect direct front/back/side comparisons. Avoid forcing side widths into the same anatomical labels.
- Next: visually identify and confidence-tag eye/nose/jaw/head/neck/shoulder/garment landmarks from verified original images; register projection and scale assumptions; then compare actual editable VRoid/stylized/CC0 candidates under identical render conditions, with independent art QA.
- Gates: G1 PARTIAL (source provenance and alpha measurement PASS, anatomical reference registration NOT_RUN), G2 NOT_RUN, G3 NOT_RUN, G4 NOT_RUN.
- This report does not adopt or replace any original asset or change main.
