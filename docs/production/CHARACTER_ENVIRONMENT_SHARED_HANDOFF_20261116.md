# CHARACTER ↔ LIND environment production handoff — 2026-11-16

**Status:** CROSS-TEAM HANDOFF / NON-CANONICAL. This is coordination, not character asset adoption, render completion, or main integration.

## Mandatory reading order
1. Latest `main:AGENTS.md` and `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`; director's latest explicit approvals.
2. Current authorized private lore main (official bible, addendum, canon status); if inaccessible, mark canon-dependent work BLOCKED.
3. Character-specific official design source, approval record, hash and current character branch/PR.
4. Shared `HANDOFF.md` and `Blender.md` for general QA and Blender reproducibility. **Their LIND world source hash, 7 map collections, metric approval and geography rules DO NOT apply to character geometry.**
5. Character-specific animation, sprite and rig contracts, verified against the actual repository and most recent accepted images.

## Shared technical conventions
- Keep canonical reference, candidate, approved production asset and technical validation strictly separate.
- Every generated asset carries source hashes, Blender version, script commit, random seed, dependency/license metadata, camera/render settings, output SHA, and G1–G4 QA states.
- No fake PASS: Blender process exit/CI success is G3 evidence only; independent art comparison is G2, runtime/Android is G4.
- Use separate work branches/Draft PRs, preserve approved PNGs and geometry. Never merge main, delete, publish or overwrite canon without explicit director approval.
- For the same root cause and same ineffective method, stop after two effective failures, document causal analysis and switch mechanism; do not reset counts via names or branches.
- Modular character rig and 4-direction artwork must not be silently replaced by world geometry scripts.

## Character-specific blockers and provenance
- Morwen approved design record: `docs/design/MORWEN_V561_CANONICAL_20261108.md`; source sheet SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`. The record explicitly says DESIGN_REFERENCE_APPROVED but production sprite NOT_APPROVED, and the original sheet binary was not stored in GitHub at the time of that record. Do not treat a similar regenerated sheet as official.
- Aidan, Fiona and Morwen's official ages are 18 (current main policy).
- Prior Morwen 4-direction walk attempts, Blender layers and renders must be audited against current branch and actual artifacts before resuming; past conversation summaries do not establish current PASS.
- No automatic import of LIND environment reference SHA into Morwen/Fiona/Aidan asset manifests.
- If current character-specific source, rig/animation dimensions, or accepted design cannot be verified, G1 BLOCKED; do not generate or mark final art as approved.

## Character ↔ environment integration interface (proposal only)
- Character deliverables: directional sprites/3D rigs, animation state IDs, anchors/pivots, nominal display sizes, shadow/contact-foot location, occlusion requirements, bounding/collision metadata and provenance.
- Environment deliverables: approved camera projection, depth-order/occlusion masks, ground contact/shadow layers, scale contract, collision and navmesh mapping, platform performance limits.
- Both teams must approve projection, visual scale and anchoring before game integration. Existing DOM pixel movement and JSON height/collision must remain unchanged until explicit adapter validation.
- Test four facings, idle/walk transitions, bridge and cliff occlusion, alpha/outline, shadow grounding, Android landscape and performance; record G4 NOT_RUN until actual device evidence.

## Status as of handoff
- Shared AI/Blender document contract CI PASS in PR #347 (run #43852084456).
- LIND handoff validator and source-review packaging are candidates in Draft PR #348; Blender end-to-end handoff has not yet been proven by a completed run.
- Character G1/G2/G3/G4: NOT_ASSESSED_BY_THIS_HANDOFF. No character files, canonical source, rig, animation or production sprites were modified.

## For the character-asset development chat
Read this document, current main AGENTS, the character-specific latest source and PRs. Reconcile any conflicting instructions. Report which exact asset SHA and render are authoritative, which gates have evidence, and what can safely be resumed without overlapping the map/world work. This handoff is informational; it does not trigger a remote AI session or grant new service permissions.
