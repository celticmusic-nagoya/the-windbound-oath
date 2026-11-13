# 3D PRODUCTION POLICY — HYBRID QUALITY FIRST / LOOP GUARD v1.0

Status: DIRECTOR-APPROVED PRODUCTION PROCESS. Applies to all future THE WINDBOUND OATH 3D characters, buildings, terrain, props and environment work. Canonical designs and asset approval still follow the latest private canon.

## Mandatory task-start checklist
1. Read current main AGENTS.md, this policy, canonical design references, and the relevant branch's existing asset manifests, scripts, QA evidence, prior attempts and pending PRs. If canon cannot be read, mark G1 BLOCKED rather than guessing.
2. Identify approved originals, references and unverified candidates separately. Record protected files and hashes.
3. State the final in-game size, view angles, asset budget, artistic target and measurable G1–G4 acceptance criteria **before** generating.
4. Search existing repository outputs and verified external assets before making new geometry. Reuse proven code and assets instead of redoing discovery.
5. Choose the method with the lowest expected total completion cost: licensed models, CC0 packs, scanned PBR, custom sculpt/mesh, Geometry Nodes, Blender Python assembly, manual techniques as needed. Never treat primitive-only blockouts as production art.
6. Record provider URL, per-asset license evidence, commercial/derivative/redistribution/attribution conditions, SHA-256, exact asset IDs, version, tools and seed. Unverified licenses mean candidate only.
7. Work in isolated candidate paths and dedicated feature branch/Draft PR. Do not overwrite canon, merge main, publish, or enable paid AI API calls without explicit permission.

## Loop prevention: required attempt ledger
Maintain a task-specific `_qa/attempt-ledger.json` or equivalent in the Draft PR, containing task ID, source SHA, method ID, input hashes, output hashes, G1–G4 statuses, visual defects, root-cause category, next action and stop reason. Update it after each meaningful attempt.

A repeat attempt is only allowed when there is a **testable causal change** to geometry, material, source, renderer or QA. Re-running identical inputs/seed/config to 'see if it improves' is prohibited. Cosmetic micro-edits without meaningful G2 benefit are not valid progress.

**At most two failed attempts per method/problem.** On the second failure, stop that method, classify root cause (shape/reference/material/structure/render/tool), compare with a different method, and switch approach or mark BLOCKED. Never reset the count by renaming the task, changing branch or moving chats.

Do not regenerate an approved part when only a different component fails. Do not report technical G3 PASS as artistic G2 PASS. If G2 fails, preserve evidence and target the failing component only.

## Four independent gates
- G1: canonical fidelity, provenance and license.
- G2: silhouette, anatomy/architecture, material and detail quality, including target in-game size.
- G3: transparency, dimensions, topology, hashes, reproducibility and render integrity.
- G4: integration, performance, mobile/Android and regression checks.

Only promote to production when all required gates pass and the director's approval requirements are satisfied.

## Handoff and continuity
Every task handoff or agent packet must link this policy, canonical reference, source asset manifest, last accepted result, last failure and ledger. Agent must resume from recorded evidence, not from a fresh unscoped brainstorm. If an expected source is unavailable, state the missing source and do not silently replace it.

## Immediate Aidan Home interpretation
Reuse `aidan_external_asset_sources.json`, `aidan_pbr_shortlist.json`, `verify_pbr_shortlist.py` and current Blender render pipeline. Prioritize licensed high-quality stone, timber and thatch meshes/PBR; texture alone cannot fix flat geometry. Current G2 is FAIL; no production promotion.
