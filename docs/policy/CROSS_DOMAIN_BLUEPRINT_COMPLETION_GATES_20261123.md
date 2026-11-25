# Cross-domain Blueprint Completion Gates — 2026-11-23

**Status:** director-approved clarification, subordinate to latest main AGENTS, Production OS, policy registry, production rules, ownership and canon. Applies to characters, environments, terrain, architecture, props, equipment, animation, UI, combat and code, with deliverable-appropriate evidence. **Does not authorize main merges of assets, canon replacement, destructive actions, public publishing, new paid tools or lease takeover.**

## Corrective purpose
A registered JSON, placeholder sheet, image trace, isolated component render, green CI or completed PR is **not** a completed blueprint or finished asset. Each production owner must close the design of the **relevant delivery scope** before new/materially changed precision production; do not force an unrelated independent module to wait. This clarifies existing mandatory blueprint-first policy in `docs/policy/TWO_PRODUCTION_OS_V1.md` and `docs/policy/ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V2.md`, without replacing VRoid-first or interrupting existing qualified work.

## Design closure D0–D4 (per asset/module/area)

| Gate | Evidence required | Fail-closed result |
| --- | --- | --- |
| D0 Source and owner | Latest canon and approved sources with SHA/licence; owning PR, HEAD, writer/lease, current Actions/artifacts; source/candidate distinction | BLOCKED / SYNC_UNVERIFIED |
| D1 Parent composition | Whole-scene/area/character composition and interfaces; final-camera targets, scale, coordinate conventions and runtime constraints; stable module IDs | BLOCKED if scope or interfaces unresolved |
| D2 Detailed drawings | Source-grounded plan, multiple elevations and sections where applicable; geometry silhouettes, landmark IDs, material/colour regions, topology/UV/rig/collision/LOD requirements as appropriate | BLOCKED for missing required views/features |
| D3 Executable targets | Machine-readable target, measurement and operation IDs; units/frame, tolerance, uncertainty, protected scope, dependencies SHA, qualified operations and stop conditions; unknowns explicit | BLOCKED or HOLD for unqualified numeric acceptance |
| D4 Independent blueprint QA | Source fidelity, drawing-to-JSON consistency, design feasibility, protected scope, parent/child and seam compatibility, explicit accepted unresolved exclusions | PASS only with evidence; otherwise BLOCKED/FAIL |

D1–D4 can be completed **per independently deliverable scope**, not necessarily for an entire game. A documented unresolved issue may be excluded only if it is demonstrably outside the affected scope and cannot affect protected geometry, canon or interfaces. A candidate-only design is not automatically a production-ready blueprint. No guessed physical measurements from 2D images.

## Domain-specific minimums

- **Character:** approved four-view/Layer0 or equivalent approved reference, proportions, face features, asymmetric hair strand/volume map, body, clothing/equipment interfaces, mesh/UV/rig/deformation targets and matched render cameras. Preserve existing Morwen VRoid-first rule: native achievable modeling and blueprint work may proceed in parallel **only for already-qualified independent operations**; new unqualified precision corrections remain gated.
- **World/area:** parent region plan and candidate geography, coast/water/drainage, contour/height and geological domains, plan/elevations/longitudinal and transverse sections, roads/navigation, architecture, vegetation, camera/light/material zones, transforms/seams and collision. Major cliffs/overhangs use authored mesh/sculpt; gentle slopes may use heightfield; GN scatter must respect exclusions.
- **Architecture/props/equipment:** whole-object composition, orthographic plan/elevations/sections, dimensions/joins, materials, UV/texel density, contact and LOD/collision; prevent repeating low-quality primitive trials.
- **Animation:** rig and deformation limits, key poses, root/contact trajectory, timing and state transitions; validate source pose and runtime integration.
- **UI/combat/code:** approved user flows and state contracts, interface/data invariants, test cases and acceptance thresholds; use testable specifications rather than forcing irrelevant 3D drawings.

## Production after design closure

1. Compare to existing qualified native candidates; reuse SHA-matched stages and avoid wholesale rebuilds.
2. Execute approved non-destructive edits in the existing owning PR with a single writer and verified controller/CAS/fencing.
3. Measure residual r against tolerance t and uncertainty u: r+u <= t PASS, r-u > t OUTSIDE, else HOLD. No unqualified auto-correction.
4. Save/reopen native, matched-camera render, independent art and technical QA, game/runtime QA and G1–G4. Blueprint D4 PASS is **not** G2–G4 PASS or formal adoption.
5. Report **design maturity separately from production maturity**; for BLOCKED specify missing evidence and continue only independent safe work. Do not create empty diagrams or repeated audit files as substitutes for design closure.

## Immediate application

- **Cliff PR #421 / regional PR #364:** finish source-grounded whole-area master and per-asset blueprints; prior pixel traces and section slots are partial evidence only. Do not alter existing C13/E/C12 production writers or their artifacts.
- **Character PR #427:** audit character blueprint completeness with current owner, retain VRoid-first and protected Layer0; do not duplicate authoring.
- **Common engine PR #468:** reuse current Blueprint/Factory/QA systems; do not implement a second validator or controller.
- **All other area and asset owners:** add D0–D4 design status to existing PR handoffs and enforce gates before newly affected precision authoring. Existing qualified independent work continues.

**Adoption:** this policy is a gate clarification only. Formal asset adoption and merges require their separate approvals and full applicable QA.
