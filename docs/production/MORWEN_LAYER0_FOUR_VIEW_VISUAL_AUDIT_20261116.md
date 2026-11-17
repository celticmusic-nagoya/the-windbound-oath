# MORWEN Layer 0 — four-view visual inspection — 2026-11-16

**Evidence:** The four PNGs in `assets/canonical/morwen/2026-11-16/` were fetched and visually inspected from GitHub at the character branch. This is a reference observation, not new geometry, approval of art or QA PASS.

## Observed, not inferred
| Area | Front | Back | Facing right / left |
|---|---|---|---|
| Hair | Purple chin-to-neck-length bob, bangs with uneven strand grouping and central crown part | Layered tapered bob ends around nape, irregular strand groups | Side locks near cheek and ear, rear hair volume visible; sides are not to be treated as pixel-perfect mirrors |
| Face | Purple irises, straight relaxed neutral gaze, narrow nose and small mouth | Not visible | Nose/chin projection, ear and side locks legible |
| Body | Neutral A-like relaxed stance, arms down, feet close together | Shoulder blades, waist, hips and calves visible | Front/back body depth and shoulder/hip silhouettes visible |
| Layer 0 clothing | Purple/gold decorative bra and matching briefs; dark purple knee-high hosiery | Straps, rear fastening and lace pattern visible | Strap routing, garment depth and leg coverage visible |
| Asymmetry | Suspender/garter strap on character's anatomical right leg (viewer left in front view) | Strap on viewer right in back view | Facing-right view exposes garter on near/visible right leg; facing-left view mostly hides it |
| Feet | Covered by hosiery; toes/foot contour visible | Heels and hosiery visible | Toe and heel silhouette legible |

## Explicit restrictions
- These images are **Layer 0 undergarment/inner construction references**, NOT evidence that the final game costume is underwear-only. Outer academy uniform, headwear, emblems, book and other accessories require their own approved full-costume references before modelling.
- The images show a visible gradient behind the figure; whether those background pixels have nonzero alpha must be determined by image measurement, not inferred from RGBA file mode or visual display.
- Four views are illustrative and may have projection or silhouette inconsistencies. Do not use one view as exact physical orthographic measurement without checking front/back/side consistency.
- Source references are distinct from the older main v5.61 image; canonical precedence G1 remains BLOCKED until formally reconciled. Preserve both originals.

## Concrete character mesh work packages
1. **HEAD / HAIR:** build facial planes and layered asymmetrical hair locks as separate mesh groups; compare front crown/bang shapes, back nape taper and both cheek/ear side silhouettes.
2. **BODY:** reconstruct proportional landmarks only after measuring actual reference pixels. Use sculpt + manual retopology for clean shoulder/hip/knee/elbow deformation; avoid generic primitive-body substitution.
3. **INNER / HOSIERY:** separate PBR cloth surfaces, purple/gold trim, strap hardware and right-leg garter. Keep asymmetric attachment and clothing intersections testable; preserve skin/cloth material boundaries.
4. **OUTER OUTFIT:** BLOCKED pending inspection of approved full-costume references. Do not infer outer costume from Layer0.
5. **RIG:** retain candidate-only evaluation until geometry is accepted; measure toe/heel contact and knee/elbow deformation independently.

## Gate status
- Source files visibly inspected: **DONE** (human-readable reference observation only).
- Manifest SHA validation on actual fetched binaries: **NOT_RUN in this inspection**; workflow can perform it.
- G1 canonical precedence: **BLOCKED**.
- G2 3D model art conformance: **NOT_RUN**.
- G3 actual new mesh/render: **NOT_RUN**.
- G4 game/Android: **NOT_RUN**.

Next evidence: execute the Layer0 silhouette script in Actions; compare alpha/background and quantify reference landmark alignment. Do not promote a candidate or overwrite originals.
