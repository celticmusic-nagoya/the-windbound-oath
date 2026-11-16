# MORWEN TURNAROUND V1 — independent visual QA
Date: 2026-11-16
Status: FIX REQUIRED; NOT ADOPTED

## Inputs
- Canonical 2026-11-16 design JPEG and Layer0 front/back/profile PNGs, stored under `assets/canonical/morwen/2026-11-16/` (source registration verified 5/5 in PR #339).
- A newly generated V1 composite turnaround shown in the ChatGPT conversation. **This generated image is not committed to this PR**, so no file SHA, automated image comparison or pixel-based head ratio measurement is claimed.

## Findings
| Check | Status | Basis |
|---|---|---|
| Face, bob haircut, glasses | PARTIAL | Major features recognizable; detailed fidelity not certified |
| Hat, uniform, cape | PARTIAL | Broad costume and palette preserved; view-to-view consistency unverified |
| 7.75-head proportion | BLOCKED | Printed label only; no calibrated pixel landmarks or measurements |
| Orthographic 4-view alignment | FAIL | No proven shared geometry or calibrated landmarks; unsuitable as precise production turnaround |
| Anatomical right-leg garter | PARTIAL | Appears in front/back details, but continuity and side geometry not independently established |
| Direct Blender modeling source | FAIL | Missing measurement/geometry correspondence across views |

## Gates
G1 FAIL for production reference eligibility; G2 PARTIAL (visual direction, not approved independent art pass); G3 NOT_RUN (no geometry or measured image validation); G4 NOT_RUN.

## Corrective method
Stop unconstrained regeneration of full composite sheets. Establish fixed landmarks (vertex of head, chin, shoulder, bust, waist, crotch, knees, ankles, floor) with common 7.75-head scale and consistent orthographic camera, then generate or draw individual front/back/right/left view candidates, retaining the 2026-11-16 approved design and anatomical right-leg, rear-visible garter. Review independent views and only then compose the final sheet. Do not overwrite canonical originals or merge to main. No approval to promote V1.
