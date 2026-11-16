# MORWEN EYELID-09B | Collision QA decision

Source: GitHub Actions run 43784347370, job 133028510578 (Blender 5.3 headless).

## Verified
- Baseline world-up strips: R 59, L 64 cage triangle pairs, total 123.
- Local-frame candidate 09: R 0, L 17, total 17.
- Endpoint-normal continuity candidate 09B: R 0, L 4, total 4.
- Residual collision remains exclusively M09_L_LASH_CANDIDATE_00.
- Eye surface overlap remains zero in these BVH checks.
- Endpoint-normal continuity reduces residual overlap by 13/17 pairs; it does not prove root normal discontinuity was the sole cause.
- Workflow fails intentionally at Gate endpoint candidate 09b. No technical G3 PASS.

## Attempt accounting / stop condition
- World-up scaffold (original) retired.
- Local tangent/normal frame (09): first structural attempt, 17 pairs.
- Endpoint normal continuity (09B): one targeted correction, 4 pairs.
- Do NOT generate additional normal-weight, offset or thickness parameter variants under the same approach without new evidence. Repeated parameter nudging is not a new root cause.

## Next distinct structural investigation
1. Inspect the actual 4 intersecting cage triangles and which of the five faces of LASH_CANDIDATE_00 are involved; compare world-space coordinates and normals.
2. Check root containment and nearest-point signed clearance independently of BVH triangle-pair overlap.
3. If intersection is confined to the first face, redesign the root attachment as a cage-surface-conforming ribbon with explicit outward clearance. If intersections persist beyond the root, change the strip centerline construction to a curve constrained to a safe envelope. These are alternatives, not approved solutions.
4. Re-test original and candidate on the identical contact-cage model SHA. Require no overlaps, containment, swept closure, four-view art and 48px readability before final G3/G2/G4 claims.

## Gates
G1 BLOCKED (official image binaries unavailable for hash verification).
G2 NOT_RUN.
G3 FAIL (4 cage surface triangle pairs).
G4 NOT_RUN.

Candidate only. No original assets, main, publication or game integration changed.
