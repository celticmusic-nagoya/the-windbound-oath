# TWO 3D Production Quality-First Protocol v1 — working standard

**Scope:** character, hair, costumes, props, buildings, environment, map, animation. Applies to Blender/Python/GitHub Actions and approved external sources. **No change to accepted canon.**

## Source hierarchy
1. Explicitly director-approved originals / locked design specifications and hashes.
2. Registered approved views, palettes, dimensions, asymmetry and anchor points.
3. User-supplied target sheets (until explicitly confirmed canonical).
4. External references and third-party model candidates, never canonical by default.

Maintain a source register: source URL, author, license version, attribution requirements, commercial redistribution permissions, SHA-256, provenance, modifications, and approved usage. **Do not import game/VTuber/Vocaloid assets simply because they are downloadable.** Inspiration and study are not redistribution rights. Commercial use, modification, and redistribution must be individually verified. Unverified items stay research-only.

## Preferred pipeline
1. **Definition of done before geometry:** target platform/render size, orthographic views, silhouette, silhouette asymmetry, target triangle/material/texture budgets, rigging requirements, G1-G4 criteria.
2. **Reuse-first survey:** compare legally reusable CC0/CC-BY/permitted model bases, geometry nodes, sculpted parts, procedural generation, and targeted hand modeling. Record decision and why. Do not force Blender Python alone or primitives-only modeling.
3. **Canonical fit analysis:** compare 4-view silhouettes, proportional landmarks, topology/connected components, materials, UVs, articulation, render consistency; annotate measurement confidence and reference-image limitations.
4. **Part-oriented production:** independent face, eyes, hair locks, clothing layers, ornaments, architecture details, terrain and collisions; establish scale and anchor coordinates. Preserve immutable source and separate original from derivative.
5. **Automated technical QA:** verify source hashes, non-manifold/loose geometry, normal direction, UV, alpha, seams, symmetry/asymmetry, rendering, performance; generate inspectable renders and machine-readable JSON.
6. **Independent visual QA:** actual in-game scale and 4-view visual comparisons; judge silhouette, anatomy, material response, finish and aesthetic cohesion. Technical PASS is **not** G2 approval.
7. **Integration QA:** device/Android performance, collision, animations, compatibility and regressions. Only approved assets may replace production originals.

## Anti-loop rules (mandatory)
- **Maximum 2 failed attempts for the same defect with the same technique.** Stop after failure 2. A small prompt/parameter adjustment does **not** reset the count.
- Every attempt must specify hypothesis, changed method/parameter, expected measurable result, rendered evidence, actual delta, and failure category.
- After failure 2, switch the **method** (e.g. VRoid local tweak -> constrained retopology or sculpt from canonical multiview; primitive cottage -> licensed mesh kit + bespoke roof sculpt), not merely percentages.
- If no viable alternative with sufficient evidence, mark BLOCKED and request a genuinely missing decision; never loop through near-identical renders.
- Reuse geometry only when baseline is structurally compatible. A fundamentally mismatched head, roof, or costume is not a candidate for incremental repair.
- Stop spending work on marginal fixes with little final-quality gain. Prioritize a production-quality master and modular reuse.
- **Attempt log** must include asset ID, canonical refs + hashes, attempt count, source candidate, failure classification, measurable G1-G4 outcome, next changed method. CI should reject or flag missing log when possible.
- An accepted design is LOCKED unless director explicitly changes it. No main merge, canonical replacement, destructive deletion or publishing without explicit approval.

## Immediate application
Morwen: use registered four-view Layer 0 refs for body, supplied target sheet for high-fidelity outer costume only after canonical cross-check. Candidate VRoid mesh topology is measured, but shape fidelity is **not** approved. Do not continue arbitrary jaw percentages; quantify silhouette/landmark mismatch and decide whether to rebuild the face.

Architecture: seek legally compatible stone, timber, thatch kits; use Blender modifiers/Geometry Nodes for assembly and bespoke details. Do not declare basic cubes/cylinders finished architecture.

Gates: G1 source and canon, G2 art, G3 technical, G4 runtime. Each gate is independently recorded as PASS/FAIL/BLOCKED/NOT_RUN. Production adoption requires all applicable gates PASS.

## Cross-team policy ownership and attempt-ledger compatibility (2026-11-14)

The director-approved **shared** production policy is `docs/design/3D_PRODUCTION_POLICY_LOOP_GUARD.md` (currently on `feature/aidan-home-quality-master-01`, Draft PR #295, commit `73bb498`). This document is **character-specific supplemental guidance**, not a competing global policy. Consult the shared policy before work; do not assume it is present on this branch or main until merged.

The existing character validator `tools/blender/morwen_production/validate_attempt_log.py` uses `TWO-3D-ATTEMPT-LOG-01` and validates a narrower subset of the shared ledger fields. Shared policy additionally requires task ID, source/input/output hashes, method ID, visual defects, root cause, next action and stop reason. **Compatibility remains PARTIAL** until an adapter and tests are implemented. Do not claim cross-chat attempt history is automatically unified.

When transferring a task between chats or branches, carry the original ledger and cumulative attempt counts; renaming a method without a causal change does not reset failures. Preserve current Morwen canon and approved images. Never copy or merge other branch changes automatically.

### Shared ledger implementation status (2026-11-14)

`tools/blender/morwen_production/validate_shared_attempt_ledger.py` validates `TWO-3D-SHARED-LEDGER-01` with task, asset, defect, method family, input/output hashes, source, defects, root cause, stop reason and G1–G4. A method rename does **not** reset counts when `method_family` stays unchanged. The second failure requires a stop reason; a third failed attempt in that family is rejected. Tests: `python -m unittest discover -s tools/blender/morwen_production -p 'test_validate*ledger.py' -v`. Existing narrower `validate_attempt_log.py` is retained for backwards compatibility. Historical ledgers have **not** been migrated; cross-branch automatic synchronization remains NOT_IMPLEMENTED. No model has been modified.
