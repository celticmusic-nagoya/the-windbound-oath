# LIND HOME ↔ BUILD pre-integration audit (2026-11-17)

Scope: read-only comparison of the **actual** published branch documents; no generated model or image inspected.

## Sources

- `feature/lind-home-01:docs/production/lind/home/ARCH_KIT_CONTRACT_V1.md` (HOME contract candidate, machine-readable JSON wins on disagreement).
- `feature/lind-buildings-01:docs/production/lind/buildings/BUILDING_PROGRAMME_V1.md` (BUILD programme candidate).
- `feature/lind-ecology-01:assets/candidates/LIND-ECO-01/eco_kit_v1/renders/renders.json` (2 render names, Blender 5.3.0, SHA records; **not visual inspection**).

## Finding 1 — incompatible origin conventions: BLOCKED for scene assembly

HOME: origin = center of exterior footprint bounding box; z=0 at finished exterior grade by main door. Main entrance faces -Y.

BUILD: origin = front-door threshold center; Z-up, 1 BU=1 m, front=-Y.

These two local coordinate frames are not equivalent. The integrator must not silently align them by assuming same origin. BUILD must explicitly adopt the HOME candidate convention or publish a reversible transform for each building, with a versioned anchor test. Neither contract is locked canon.

## Finding 2 — BUILD says HOME contract unavailable: stale dependency

BUILD programme says HOME arch-kit contract not published and values in `kit_config.py` are pending alignment. HOME has since published `ARCH_KIT_CONTRACT_V1.md` and `arch-kit-contract.v1.json`. Before more BUILD generation, compare BUILD's current config/kit against the JSON values and produce a machine-readable mismatch report; do not overwrite BUILD dimensions without reviewing intended variants.

## Finding 3 — roof pitch and scale are proposals

HOME blue-gray slate roof pitch 38–48°, default 42°; BUILD visually proposes ~45–50° from approved CG. Overlap exists, but 50° exceeds HOME's candidate range. Both are non-canonical proposed geometry values. Require per-building overrides with documented reasons; do not promote visual estimates to official specs.

## Finding 4 — ECO renders exist, not independent G2

The ECO renders manifest lists `eco_lineup_large_wind0.png` and `eco_lineup_small_wind0.png`, with SHA values and Blender 5.3.0. No visual inspection or independent art QA was executed in this audit; G2 NOT_RUN. For G2 review, fetch the actual PNGs and assess target-size readability, vegetation silhouette, leaf cards/alpha, branch repetition, water and wind effects where present. Do not infer asset quality from manifest hashes.

## Required non-destructive next steps

1. HOME/BUILD owner: choose a shared **candidate** origin convention and provide an explicit transform/anchor validation test. Until then, cross-building assembly BLOCKED.
2. BUILD: diff all dimensions/material IDs/roof rules against HOME JSON, report mismatches; keep its authored variations independent until reviewed.
3. ECO: submit actual rendered PNGs for independent visual review and separate alpha/material QA.
4. All: use provisional coordinate space, no world-map metric lock, no canon replacement or main merge. Save producer/consumer SHA and Blender version. G1 spatial BLOCKED, G4 NOT_RUN.

This audit changes no HOME, BUILD, ECO, WORLD, ROUTE source files or production workflow.
