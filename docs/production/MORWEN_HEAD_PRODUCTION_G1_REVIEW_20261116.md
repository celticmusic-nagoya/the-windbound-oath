# MORWEN-HEAD-PRODUCTION — G1 reference discrepancy review

**Status: BLOCKED for production head/body sculpt; technical reference work may continue.**
**Inspection:** actual 1536×1024 director-submitted JPEG design sheet viewed in full, not inferred from filenames.

## Confirmed visual requirements from the sheet
- Four clothed character views: front, right, back, left; plus face close-up, expressions, ornament detail, and four Layer0 underwear references.
- Purple short bob with straight bangs and longer face-framing locks; round gold-rim glasses; violet eyes; small floral hair ornament near ear.
- Tall asymmetric purple witch hat with gold edging, large floral arrangement and hanging faceted crystal ornament; retain right/left orientation.
- Purple academy outfit with gold trim, cloak/mantle, crest (open book inside laurel wreath), diagonal brown shoulder strap, satchel, vials, pleated skirt, thigh-high stockings and buckled boots.
- Preserve accessory asymmetry and anatomical right-leg garter according to canonical manifest.
- The design sheet labels its four-view figure as the intended formal design; its Layer0 references are not a finished clothed 3D model.

## Critical proportion conflict
The sheet's illustrated full-body silhouette is stylized and visibly has a substantially larger head relative to height than a realistic **7.5–8 head** target. The director also explicitly replaced the old 2.8-head sprites with high-quality full 3D at 7.5–8 heads. A direct tracing of the sheet and strict 7.5–8 heads cannot both preserve every illustrated proportion.

**Do not silently resolve by changing the head, hat, face, costume proportions or claiming G1 PASS.** The geometry guides are technical coordinate aids only; no anatomical landmark or proportional conformity has been independently established.

## Safe production decision
1. Preserve the sheet as **identity, hairstyle, colors, clothing, asymmetry and accessory canon**.
2. Preserve 7.5–8 heads as a **separate director-requested target**, not as a measured fact of the sheet.
3. Require a newly director-approved realistic-proportion orthographic character turnaround, or an explicit approval to adapt the illustrated sheet to 7.5–8 heads, **before locking final body/head geometry**.
4. Independently sculpt/retopologize high-quality head, face, hair and outfit only after proportions and facial identity are resolved. No generic primitive mesh is final.
5. Existing four-view Layer0, silhouette envelope and reference scene remain non-destructive technical evidence; no source overwrite.

## QA state
- Source files and SHA checks: PASS (as reported by latest successful CI).
- G1 full canonical/proportion conformity: **BLOCKED**.
- G2 independent artistic review: **NOT_RUN**.
- G3 silhouette-envelope topology: **PASS_TOPOLOGY_ONLY**; final character mesh **NOT_RUN**.
- G4 game and Android: **NOT_RUN**.

**Decision needed:** director confirmation of 7.5–8-head reinterpretation of the pictured design or approved 7.5–8-head orthographic turnaround. No main merge, publication or canon replacement.
