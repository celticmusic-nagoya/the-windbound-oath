# Character production parallel handoff v1 — for separate character asset chat
Status: DRAFT coordination only; no character files modified or produced.

## Before any modeling
Read main/AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md; inspect the character-specific canonical reference files, 4-view Layer 0 and approved designs and current PR/attempt ledgers. Preserve Morwen/Fiona and any accepted directional art. If source cannot be accessed, G1 BLOCKED; never infer the missing face or costume detail.

## Lock interface once, then work independently
Shared schema (values to be obtained from approved sources, not invented): character ID, canonical head-to-body ratio, unit scale, origin, coordinate axes and camera, 4 directions, reference hashes, pose (neutral T/A), head-to-neck seam position, shoulder/waist attachment, body UV and material slots, armature bone names, facial expression controls, clothing layer order, occlusion masks, equipment slots, LOD and sprite export sizes.
No producer changes this schema without a reviewed interface-change PR.

## Parallel tracks
FACE: head topology, eyes, mouth, ears, hair/ornaments, expressions; independent preview turntable and direction views.
BODY: torso, limbs, hands, feet, skin/deformation, contact pose and rig; independent geometry/weight QA.
COSTUME: innerwear, outerwear, socks, shoes, belts, accessory/equipment; verify against exact official artwork. Keep independent Blender collections, materials, masks and attachment contracts.
INTEGRATION: non-destructive assembly, clipping/occlusion QA, animation and 48px game-size readback. Do not start final integration until interfaces are compatible.
INDEPENDENT QA: checks each track's mesh manifoldness, UV, material alpha, skin weights, silhouettes, visual correspondence and regression. No producer self-review can certify G2.

## First assignments
1. FACE-BASE: audit official face/head four-view refs and generate the face module specification only after canonical verification.
2. BODY-BASE: audit Layer 0 and rig interfaces and generate body module specification only after canonical verification.
3. COSTUME-BASE: inventory exact official costume components and occlusion hierarchy; no speculative additions.
4. Integration QA: compare interface manifests; only proceed when no contradictory scale/origin/bone names.

## User-facing agent instruction
In the character asset chat: “Read docs/production/CHARACTER_PARALLEL_HANDOFF_V1.md and docs/production/AI_PARALLEL_ASSET_TEAM_V1.md on the coordination Draft PR. Audit canonical character art and current PRs, then split face, body and costume into independent branches with a shared immutable interface contract. Proceed non-destructively; do not merge main, overwrite approved designs, or claim unrun Blender/G2/G4 tests as PASS. Report exact task IDs, PRs, hashes and blocked canon references.”

Note: This document does not automatically notify another chat or launch Claude/Codex sessions. The user must paste the instruction or connect/run those sessions.
