# COMMON-RIG-01 — Shared Blender rig architecture (proposal)

Status: DESIGN_ONLY. This file does not authorize production art replacement.

## Architecture
- Common motion skeleton: `root`, `pelvis`, `spine`, `neck`, `head`, `upper_arm.L/R`, `forearm.L/R`, `hand.L/R`, `thigh.L/R`, `shin.L/R`, `foot.L/R`.
- Character profiles define normalized bone lengths, facing-specific art layers, per-facing pivots, draw order and costume attachments.
- Motion clips are independent of character art; use normalized angles/offsets with retargeting constraints.
- Never mirror asymmetric costume art or generate unapproved rear-side details.
- Keep `profile`, `motion`, `renderer`, and `qa` as separate modules.
- Exports go to candidate-only output, never `assets/official`.

## Morwen pilot
- Source categories: four clothed turnaround references, separate proportion references, HD v2 pixel originals. Do not combine into one assumed canonical image.
- Preserve official bob, purple hat, glasses, knee socks, book and handed accessories as supported by approved art.
- Main v5.61 design sheet `7374.png` remains unverified as a binary.
- First proof: common armature data validation + one neutral front-facing **rig-only** test; do not claim this represents approved Morwen pixels.
- Only after source lock and director review: a candidate 48×64 sprite with shared ground anchor (24,63), 4-direction loops and pixel QA.

## Gates
1. Blender smoke workflow green with saved .blend and QA artifact.
2. Rig definition schema and left/right bone symmetry tests green.
3. Canon source mapping and attachment positions verified by human review.
4. One candidate frame generated, alpha and silhouette QA green.
5. Director visual approval before animation expansion, integration or merge.

## Cost and operations
- GitHub Actions uses manual or PR-scoped triggers, read-only repository permission.
- No API secrets, AI calls or automatic publication.
- Pin Blender version after first successful runtime; avoid silently changing renderer behavior.
