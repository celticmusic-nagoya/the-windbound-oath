# MORWEN-EYELID-SCULPT-06 — corrective eyelid shape-key design gate

Status: DESIGN ONLY / NOT ADOPTED. Parent: PR #318 HEAD 357814f235e61bf77f55c2ce53f46d4f64104f23. Do not merge to main.

## Evidence and scope
- Input: `eyelid_retopo/eyelid_params_05.json`, `EYELID_05_REPORT.md`, `_qa/eyelid_retopo_05/`. The new canthus-anchored static quad strips are retained; they match the Layer 0 opening (22.0 × 10.81 px versus 22.0 × 10.4 px target) and pupil spacing within 1 px.
- Do not reuse either stopped deformation family: VRoid (u,t) key transfer A1/A2; analytic canthal/eyeball pivot rotation B1/B2.
- Do not alter the Layer 0 source, 56 shape-key names/order, #312 nose depth 0.5, mouth, body, violet eye material or face/body seam. Preserve existing trial ledgers verbatim until actual new trials occur.
- Full canon G1 remains BLOCKED without the v5.61 reference.

## Art target before implementation
A closed-eye target is a separate *candidate*, not canon. Produce a front-view and both 45° view curve overlay with paired upper/lower lid margins, fixed inner/outer canthi, and a smooth single continuous closure line. At the midpoint, upper and lower margins meet without leaving visible sclera/iris; avoid a central V, a shelf, and a sharp tangent discontinuity at the canthi. Evaluate neutral, full Blink, left/right wink, Joy and Blink+Joy; do not infer that numerical symmetry implies canonical intentional symmetry.

Use the measured Layer 0 opening curve as the neutral anchor, then author a closed target curve in normalized arc-length u ∈ [0,1]. Store both target samples and the authoring rationale in a JSON file *after* inspecting render overlays. Do not silently invent final target samples from this specification. Confirm eyelash/eyeline cards follow the skin surface in all tested views.

## Implementation strategy
1. Generate a deterministic Blender baseline from the unchanged #318 candidate, record Blender version and SHA hashes.
2. Author upper/lower closure targets on the existing quad strips as localized corrective shape-key deltas. Preserve canthus endpoints, maintain monotonic u, and interpolate the 3 interior t rows with smooth falloff toward the untouched outer boundary.
3. Use localized corrections for Blink, Blink_L, Blink_R and Joy without changing key names/order; avoid transfer from the old VRoid lid or rotation about the old canthal axis. Ensure combinations do not sum into self-intersections. Treat the remaining expression keys as regression checks.
4. Preserve eyelid thickness and card rebind without exposing the eye socket at 45°. Do not adjust unrelated mouth/face vertices.
5. On two failures in this method family, stop corrective-shape-key attempts, record evidence in both ledgers, diagnose the root cause and move to a separately designed bone-rig family. Do not loop the same generator.

## QA and evidence required
- G1: SHA and protected-region equality, Layer 0 overlay, 56-key identity/order, full canon status explicitly BLOCKED until source obtained.
- G2: independent artistic review of neutral/Blink/wink/Joy/Blink+Joy, front, both 45°, and profile; full-resolution and 128/64/32 px on a *composited* nonblack game background.
- G3: zero inverted faces, zero 45° show-through rays, zero visible eyeball samples in fully closed state, no card penetration, no V-shaped crease, no unacceptable edge stretch; preserve all-quad topology and UV winding. Validate against actual recorded baseline thresholds rather than inventing pass values.
- G4: game integration and Android device QA NOT_RUN until performed.
- CI: deterministic render and numerical report, compare local and GitHub Actions evidence, archive provenance, hash manifest and images. CI success alone is not G2/G3 PASS.

## Current checklist
- [x] PR #318 report and parameter file inspected
- [x] Separate development branch created
- [x] Method-switch design recorded
- [ ] Closed-lid art curve authored/reviewed
- [ ] Blender shape-key build implemented
- [ ] CI/render evidence generated
- [ ] Independent G2 and G3 PASS
- [ ] G4 game QA
