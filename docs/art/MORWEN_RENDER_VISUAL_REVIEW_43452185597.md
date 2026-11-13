# MORWEN-RENDER-VISUAL-REVIEW-01 (2026-11-14)

## Evidence
- GitHub Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43452185597 — **SUCCESS**, commit `18a6ad91e9729b0748683e905e96292ac3082dea`.
- Artifact `morwen-vroid-cc0-head-review` ID `14051722153`, 11,299,137 bytes, digest `sha256:23e2fb3448a31ae3f131c798b5d25f7868551d0db630a78092cdb347c0f11c17`.
- Inspected actual PNGs: `MORWEN_HEAD_FOCUSED_COMPARISON.png`, `MORWEN_REFERENCE_VROID_COMPARISON.png` (both 2304×768).
- Machine status: `COMPARISON_STATUS.json` canonical_match=NOT_APPROVED, landmark_alignment=NOT_DONE; `HEAD_COMPARISON_STATUS.json` landmarks_aligned=false. `FACE_CANDIDATE_QA.json` topology_unchanged=true, canonical_likeness=NOT_ASSESSED.

## Visual review (qualitative, not calibrated)
Reference shows violet shoulder-length layered bob with bangs, large purple eyes, tapered soft face, more mature body proportions, ornamented undergarments and tall stockings. Candidate has cyan short swept-back hair, amber eyes, different eye/face expression, and school-uniform upper body. These differences are conspicuous at normal viewing size and **not** evidence of successful character likeness.

Face mesh anatomy may still be a candidate for a structural base, but **no reuse approval** is justified from this comparison because hairstyles, eye shapes and chin/cheek landmarks are not aligned or quantitatively annotated. The left/right reference crops and candidate renders are not anatomically registered. Clothing and hair in the candidate are not canonical Morwen assets.

## Decisions
- G3 **PASS for this CI rendering/topology pipeline**, not finished production mesh.
- G2 **FAIL for direct visual reuse of current candidate as Morwen**. Face topology `REUSE_OR_REBUILD_UNDETERMINED` until neutralized head landmark comparison.
- Stop arbitrary local jaw-percentage adjustments. First isolate skin head mesh, hide candidate hair/clothes, align head cameras and compare eye/nose/chin landmarks to approved front/right references; if structural mismatch remains, switch to sculpt/retopology.
- Create independent hair, hat and clothing from approved reference geometry; do not use candidate cyan hair or school outfit as Morwen final.
- No attempt count is inferred from prior unitemized work. New attempts must use canonical `schema_version:1` ledger.

## Gates
G1 PARTIAL: Layer 0 source images verified by workflow; full-costume target binary GitHub registration pending.
G2 FAIL for candidate likeness; neutral-head fit review NOT_RUN.
G3 PASS for run's renders and topology checks only.
G4 NOT_RUN. No canonical files changed, no integration or publication.
