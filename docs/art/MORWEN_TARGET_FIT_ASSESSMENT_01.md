# MORWEN-TARGET-FIT-01 — Visual fit assessment and modeling decision

Status: **REFERENCE-BASED ANALYSIS ONLY — no new model or render approved**.

## Inputs
- Director-supplied image (2026-11-13): 1536×1024 JPEG SHA-256 `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b`, local upload `7855.png`; see `MORWEN_3D_TARGET_SHEET_20261113.md`.
- Existing canonical Layer 0 references: `7809.png` front, `7807.png` right, `7810.png` back, `7808.png` left. These are **distinct images**.
- VRoid candidate topology: `MESH_QA_01_FINDINGS.md`, `MESH_QA_02_COMPONENT_FINDINGS.md`. Topology measured, visual fit NOT APPROVED.

## Target sheet analysis
1. **Face:** oval/soft jaw, small nose and mouth, large violet eyes; delicate glasses. Test frontal and profile silhouette against the Layer 0 head, not arbitrary jaw taper.
2. **Hair:** layered violet bob with bangs and distinct side locks, consistent from four views. Model as separate clumps with thickness and controlled highlights; avoid flat intersecting cards.
3. **Hat:** asymmetric wide brim, pointed folded crown, gold filigree and flowers, hanging faceted pendant. Separate geometry for crown, brim, trim, ornaments and flower.
4. **Cape/outfit:** tailored deep-purple tunic with gold edges, academy shoulder insignia, pleated skirt, cloak/cape layers and embroidered hem; separate cloth thickness and material slots.
5. **Props:** diagonal satchel strap, book-marked shoulder motif, pouch, two potion vials, belt buckles, lace-up heeled boots; preserve front/back and side placement.
6. **Layer 0:** four-view undergarment/body and knee-high stockings shown in lower right. **Do not conflate with finished outfit.** Check approved asymmetry against canon.
7. **Rendering:** soft key/fill/rim lighting, clean specular differentiation for satin, leather, gold, skin and hair. This is a target look, not a claim that current mesh achieves it.

## Modeling decision gate
- Current VRoid candidate has measured topology but **no evidence of canonical face fit**. Repeated local jaw percentages are prohibited until orthographic front/profile comparison establishes a suitable base.
- Keep or adapt the candidate only if major proportions, eye/nose/chin landmarks and 4-view silhouette can be matched without structural distortion.
- Otherwise switch to new face topology / sculpt-retopology and use candidate solely as anatomical reference if license permits.
- Build outer costume, hat and hair as **independent high-quality geometry**, not primitive proxy as finished model.
- Do not infer precise physical measurements from a stylized, non-calibrated render sheet.

## QA plan
G1: canonical reference SHA and approved asymmetry; G2: side-by-side full-body/head views and final-scale render; G3: topology, UV, texture/alpha, rig deformation and reproducibility; G4: browser/Android runtime budget and animation.

**Current gates:** G1 reference identities known but target binary GitHub registration pending; G2 NOT_RUN for new target; G3 candidate topology PASS only; G4 NOT_RUN.

## Next deliverables
- Upload **exact JPEG bytes** to `assets/companions/morwen/reference/morwen_3d_target_sheet_20261113.jpg`; SHA check before declaring registration complete.
- Compare canonical 4-view images with VRoid renders at calibrated scale; produce a diagnostic sheet and per-view findings.
- Select **reuse / reconstruct** on actual fit evidence. No repeated micro-adjustments.
