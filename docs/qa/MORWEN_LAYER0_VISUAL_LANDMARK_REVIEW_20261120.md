# Morwen Layer 0 — four-view visual landmark review (2026-11-20)

Status: **VISUAL REFERENCE REVIEW / BLUEPRINT PARTIAL / NO BASE ADOPTION**. Owner: existing Draft PR #427.

## Exact inspected source
- Four verified PNGs and contact sheet from Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515, artifact https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515/artifacts/14602858760.
- Source front 7809.png, right 7807.png, back 7810.png, left 7808.png, all 384x1024; original SHA256 verified by run.
- Measured alpha bounding boxes and scanline widths: `docs/qa/MORWEN_LAYER0_FOUR_VIEW_MEASURED_SILHOUETTE_20261120.md`.
- This is a **human visual inspection of the actual verified four-view contact sheet**, not an automated anatomical keypoint detector or calibrated 3D reconstruction.

## Visible design landmarks, observational confidence
| Feature | Front | Right/left | Back | Confidence and restriction |
|---|---|---|---|---|
| Cranial/hair silhouette | Rounded, voluminous violet-purple bob, parted fringe | Rounded crown and forward fringe, hair reaches nape/neck | Rounded bob with tapered inward lower tips | HIGH visual identity, but hair mass is not skull shape |
| Eyes and brows | Large stylized eyes, face roughly centered | Eye and nose profile visible | Occluded by hair | HIGH front/side visibility; exact eye coordinates NOT MEASURED |
| Nose/chin | Small stylized nose and narrow chin | Clear projected nose, lips, chin profile | Not visible | HIGH feature presence; depth is inferred, not measured |
| Ears | Mostly obscured by hair | Ear exposed in profile | Obscured | MEDIUM; ear anatomy must not be invented from occluded views |
| Neck/shoulders | Slim neck and exposed shoulder line | Shoulder, bust and neck transition visible | Exposed shoulder blades/back, two straps | HIGH broad silhouette, MEDIUM exact joint centers |
| Torso and waist | Stylized tapered waist, belly visible | Chest/waist/hip contour visible | Waist and lower back visible | HIGH contour, anatomical mesh under garment remains inferred |
| Hair asymmetry | Fringe strands and side framing not perfectly mirror-symmetric | Both sides show different overlapping strands | Back bob outline | MEDIUM, requires high-res original close inspection before sculpt |
| Garment | Dark purple and gold decorated two-piece reference outfit | Chest/strap and hip-band profiles | Rear straps and clasp/band | HIGH; **reference outfit only**, not authorization to replace final Layer 1–3 costume |
| Accessory | Hanging narrow decorated strap and buckle on one visible thigh | Hanging accessory visible in profile | Rear belt/strap position visible | HIGH presence, MEDIUM exact attachment and character-left/right assignment |
| Legs/feet | Thigh-high dark stockings, feet planted | Calf and foot profile | Stocking symmetry and heel outline | HIGH overall silhouette; pose/rig pivots unmeasured |

## Blueprint registration restrictions
1. These PNGs show an **illustrated stylized figure**, not calibrated photographs. Orthographic camera, absolute height, focal length and actual depth are **UNKNOWN**. Do not treat 384x1024 pixels as real-world meters or derive exact mesh vertices.
2. Preserve the observed hair volume, front/side facial identity, shoulder/waist/hip proportions, and accessory asymmetry when comparing VRoid-derived bases against independent stylized sculpts and CC0 realistic controls.
3. Use actual alpha scanlines for objective *outer silhouette* comparison. For face, eyes, nose, jaw, ear, joints and costume seams, first create explicitly labeled manually reviewed 2D landmarks with pixel coordinates, view identity, confidence, and visibility/occlusion status. None are asserted as pixel-exact here.
4. Compare candidate renders with the **same normalized subject height, orthographic front/right/back/left cameras, neutral material and lighting**, then separately evaluate 3/4 and final art material. Report silhouette IoU and keypoint error only after image registration.
5. VRoid Studio itself has **not** been run in Actions. Blender 5.3 + VRM Add-on v4.10.5 test fixture import/export/reimport/Cycles CPU render PASS in run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44678376702; this does not prove an actual Morwen-compatible VRoid source base is available.
6. Source license/adoption, topology, facial Shape Keys, hair rig, weights, UV/PBR and runtime performance require separate QA. No existing failed face-slab/voxel-head method is revived.

## G1–G4 and next executable task
- G1: **PARTIAL** — source hashes, image dimensions, alpha measurements PASS; visual identity reviewed; pixel-exact anatomical landmark table and camera calibration NOT_RUN.
- G2: **NOT_RUN** — no candidate art comparison or adopted sculpt.
- G3: **NOT_RUN** — no Morwen model rig/UV/render acceptance.
- G4: **NOT_RUN** — no in-game/Android validation.
- Next: author and visually QA an image-registered 2D landmark overlay (not fabricated 3D landmarks), then inventory actual legally usable editable VRoid/VRM candidate and compare at matched cameras. Do not create new PR or rerun successful infrastructure tests.
