# FIONA-LAYER0-MASTER-REGISTER-01

## Registration — PASS

Director-approved Fiona (18) Layer 0 source, fetched through the authenticated Google Drive connector:
`https://drive.google.com/file/d/1U2Z9bcFGvCHfSIKYjx_RGV1svj8DZ6X1/view?usp=drivesdk`.

- Destination: `assets/characters/fiona/layer0/fiona_layer0_fourview_master.png`.
- SHA-256: `faee95e9e4d9face0219318c7db3ec4847c0186b81dada9bf117d9726e70acb9`.
- PNG / 1536×1024 / RGBA / 2,114,467 bytes. Alpha range 0–254 is preserved, not normalized to 255.
- Exact byte identity with director attachment `7814.png` also verified.
- PNG registration commit: `5b3d6b973c8b3e3dae89dd75aedb33be36eea00e`.
- GitHub REST metadata/blob re-download: blob `c3333681189105b41b7dfb69a852ab060ae28507`; complete bytes, SHA, dimensions and RGBA match.
- `FIONA_LAYER0_ADOPTION.json` was changed to APPROVED / REGISTERED_GITHUB_VERIFIED only after successful binary upload and remote readback. The registration commit points to the immutable PNG commit, not to a self-referential metadata commit.
- No regeneration, redrawing, resizing, recompression, color correction, background edit, alpha edit or PNG overwrite. Registration evidence: `FIONA_LAYER0_REGISTRATION_QA.json`.

## FIONA-BLENDER-ANCHOR-01 — started after registration PASS

Files:

- `tools/blender/fiona_layer0/PIXEL_ANNOTATIONS.json`: Fiona-specific original-sheet pixel annotations.
- `docs/art/blender/fiona-layer0-anchor-01/anchors.json`: four-view landmark candidates, exact silhouette crown/contact observations, normalized sheet coordinates, uncertainty/occlusion, and common-rig adapter payloads.
- `tools/blender/fiona_layer0/COMMON_17BONE_COMPATIBILITY.json`: read-only names/parent graph from Morwen PR #246. No Morwen joint positions transferred. Per-view Fiona endpoints are mapped separately in `anchors.json`.
- `assets/candidates/fiona-layer0-anchor-01/fiona_layer0_anchor_candidate.blend`: original sheet packed byte-identically and four common-contract landmark marker armatures. This is an anchor inspection scene, not a finished 17-bone deformation model.
- `blender_qa.json`, `qa.json`, and logs in `docs/art/blender/fiona-layer0-anchor-01/`.

The existing Morwen-derived CAS common contract has **31 landmark IDs**, including pelvis. Both the contract and `shared_rig_adapter.py` remain byte-identical. The old adapter test expected 30 and failed its two count assertions before these changes; only those stale test counts were corrected to 31. All 6 existing adapter tests then PASS. The separate current 17-bone parent contract is recorded as a compatibility mapping; 31 landmarks are not claimed to be 31 production deformation bones.

### Four-view labels and geometry

Director labels remain left-to-right **front / right / left / back**. The second figure faces screen-left and the third faces screen-right; these observed screen facings are recorded independently. Anatomical L/R is not inferred by swapping label strings: front L projects screen-right; back L projects screen-left; screen-left profile has L nearer, screen-right profile has R nearer. No image is mirrored or relabeled silently.

All measurements use the unchanged **1536×1024 original sheet**, top-left origin, X right, Y down. Analysis X ranges are front `[0,448)`, right `[448,752)`, left `[752,1072)`, back `[1072,1536)`. These are analysis windows, not image crops. Equal 384px quarter cuts would clip the front figure (foreground extends to X417), so no quarter PNGs were created.

Crown and visible foot-contact observations are measured at alpha>=128. Internal anatomical joint centres are manual pixel-placement candidates with nominal review uncertainty (12px visible / 30px occluded), not independent anatomical ground truth. Hidden profile limbs, hair-covered back neck/jaw and hidden toe/ball points are explicitly inferred. Fiona's own pose, proportions, hair and approved L0 appearance are preserved; no Morwen body coordinates, hair or costume visibility rules are copied.

`cas/blender-measured/01` is the existing adapter's interface name; the additional annotation status explicitly prevents this legacy schema label from claiming that hidden anatomy was measured in 3D. Blender conversion is explicit and shared across all four views: `X=(sheetX-768)/1536`, `Z=(1024-sheetY)/1536`, `Y=0`. Marker lengths are the unchanged adapter's 0.002 guide segments; they are not inferred deform-bone lengths.

### Actual QA

- Source and registration guard PASS before any anchor generation.
- Shared adapter unit tests: 6/6 PASS. Python compilation PASS.
- Real local Blender 4.3.2 execution PASS: four 31-landmark marker armatures, common parent graph, packed original SHA.
- Saved .blend reopened in the same headless verification process: source SHA, marker count, parent graph, source-pixel projection error <0.001px PASS.
- Original PNG is untouched after Blender import; no output PNG or processed source image was generated.
- Complete deformation rig, mesh skinning, Layer 1–3 clothing construction and independent anatomical review: NOT_RUN. The 17-bone table is a compatibility candidate, not a newly approved production rig.

Reproduce:
```
python tools/blender/fiona_layer0/measure.py
python tools/blender/test_shared_rig_adapter.py
blender -b -t 1 --python-exit-code 1 --python tools/blender/fiona_layer0/build_verify.py
python tools/blender/fiona_layer0/qa.py
```

All work remains in existing Draft PR #245, branch `feature/fiona-blender-asset-01`. No existing asset modification/deletion, Morwen asset/rig modification, main merge, runtime integration or website publication. The source PNG's formal adoption is distinct from approval of candidate anchors/rigs.
