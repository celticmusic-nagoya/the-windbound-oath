# MORWEN-RIG-01 — Blender motion prototype specification

Status: **PROPOSAL / BLOCKED_CANON_BINARY**. No production sprite approved.
This document is not a replacement for the director's original artwork.

## Required sources and gates

- Re-read current `AGENTS.md`, `docs/design/MORWEN_V561_CANONICAL_20261108.md`, and `data/morwen-design-canonical.json` before creating artwork.
- Director-supplied reference `7374.png`: **actual JPEG**, 1536×1024, SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`.
- Source binary is **not in the repository**. Do not reconstruct the master from previous candidate sprites.
- Current production sprite status: `BLOCKED_NOT_YET_CREATED`.
- Canon age: 18. Keep the director-approved costume and asymmetrical accessories; no left/right mirroring shortcut.

## MVP deliverable after original binary is available

1. Verify original bytes against SHA-256, keep source immutable.
2. Create a separate **non-production** layered character rig. Layers: back hair, hat, face/glasses, torso, front/back arms, skirt, front/back legs, footwear, book, bag, accessories. Split only where physically visible; never invent hidden costume details.
3. Rig pivots and consistent ground contact. The book, bag, hat ornament, shoulder insignia and chains must be manually checked for occlusion and handedness.
4. Prototype 4 facing directions, 4 walk poses each, **48×64 RGBA PNG**, shared ground anchor **(24,63)**. These dimensions are goals, not evidence of an existing compliant asset.
5. Export to `assets/candidates/morwen-rig-01/` only. Never overwrite approved assets or production sprite paths.
6. Record manifest with source SHA, per-frame SHA, facing, index, pixel dimensions, alpha mode, ground anchor, and approval status.

## Blender / animation guidance

- Prefer orthographic 2D cutout or Grease Pencil layers; render with transparent film and no shadows/background.
- Do not use automated mesh deformation to stretch pixel-art edges. Prefer rigid layer rotation, constrained pivot movement, and manual cleanup of silhouette.
- Keep 4-frame loops stable in character scale, facing, and contact point; no unapproved costume redesign.
- When the original master is missing or a pose cannot be verified, mark `BLOCKED`, not `PASS`.

## QA gates

- [ ] Original SHA-256 matches and source is stored without modification.
- [ ] Every candidate frame is 48×64 RGBA and alpha is either 0 or 255.
- [ ] 4×4 frame count, consistent anchor and contact; left/right asymmetry manually reviewed.
- [ ] Original costume details, bob hair, large purple hat, glasses, knee socks and book preserved.
- [ ] 32/40/48px visibility QA and Android Chrome check recorded separately.
- [ ] Director visual approval before registry, game integration or site publishing.

## Stop condition

If two consecutive iterations fail the same image-quality requirement, stop generation and diagnose the source/layer/rig structure. Do not repeat the same prompt-based regeneration.

## Explicit non-goals

No canon edits, no automatic production replacement, no main merge, no website publication, no Blender render claim until Blender is actually executed.
