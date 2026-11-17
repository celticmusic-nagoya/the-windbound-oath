# MORWEN full-body base-mesh selection and measurement contract

Status: DESIGN SPEC ONLY; no purchased/downloaded mesh; no approved geometry.

## Director-approved target
Full-body 7.5–8.0 heads. Choose normalized height H=1.0, head-unit h=H/N where N in [7.5,8.0], working midpoint 7.75 (h=0.129032258H). This is **a target ratio, not a measured property of the Layer0 PNGs**. Do not assert head boundaries, limb lengths, or body landmarks from silhouette alpha bounds. Use the five immutable reference images in assets/canonical/morwen/2026-11-16/MANIFEST.json, verify SHA before production.

## Selection scorecard (must be evidenced before adoption)
| Criterion | Mandatory gate |
|---|---|
| Licensing | Document source URL, original author, exact license, redistribution and derivative rights, attribution; missing => BLOCKED |
| Editable topology | Quads around eyes/mouth/shoulders/hips/knees; suitable for sculpt/retopo; verify by opening .blend/.fbx/.glb |
| Anatomical proportions | 7.5–8 head ratio after deliberate adaptation; front/back/left/right silhouettes align to approved character design |
| Face construction | Real eye sockets and eyelid loops; reject polar annulus/zipper family, no elliptical face proxy |
| Character identity | Bob hair, eyes, round glasses, asymmetrical hat, costume, straps, right-leg garter, socks, boots, crest |
| Game use | Rig-compatible, bake/retopo possible, legal WebGL distribution, Android budget tested rather than guessed |
| Provenance | SHA-256 of downloaded file and import scripts; tool version and seed recorded |

## Candidate classes (NOT endorsements)
A. Existing **licensed sculpt-ready stylized human base**: preferred if anatomy, topology, redistribution rights and look can be verified.
B. Blender sculpt-ready generic human mesh: fallback if A cannot meet legal/identity constraints; requires deliberate character sculpt.
C. Prior 6.57-head CC0 VRoid candidate: **technical reference only**, not preferred as final and not automatically reusable.
D. Parametric ellipsoid head + tubular hair: **rejected final-art method**; keep evidence.

Do not download or commit external asset until its licensing is verified. Do not mislabel an uninspected candidate as PASS.

## Landmark contract
Record for each view: foot plane, top of skull **excluding hat**, chin, shoulder line, elbow, wrist, waist, crotch, knee, ankle; hat top and hair silhouette as separate accessory landmarks. Every landmark: image pixel, normalized Y, method (manual/verified), reviewer, confidence and source hash. Until inspected, all landmark coordinates = NOT_MEASURED. Do not infer them from the overall alpha bounding box.

## Workflow and gate order
1. Existing artifacts and prior failed-method ledger inventory, including eyelid/eyelash/nose source meshes and nose depth=0.5.
2. Basemesh licensing and topology evidence; record version and SHA.
3. Design-aligned front/side/back silhouette review and facial anatomy. G1 can only pass after visual source comparison.
4. Independent G2 art review; then retopo, UV/PBR, rig deformation G3 and Android/WebGL G4.
5. Director explicitly authorizes canonical promotion/main merge/release; none implied here.

## Current evidence
- Source SHA manifest available; 4 Layer0 images 384x1024 and one design JPEG 1536x1024.
- Legacy eyelid/mouth polar annulus failed twice (face fold and UV inversion).
- Prior head/hair render 5 views delivered in run 43866841140 but G2 FAIL; visibility gate newly added and not yet verified in Actions.
- No high-quality base mesh obtained or validated. G1 BLOCKED; new G2 NOT_RUN; new G3 NOT_RUN; G4 NOT_RUN.
