# FIONA-MORWEN-RIG-COMPAT-01

Status: **AUDITED / ADAPTER_PENDING / NOT_ADOPTED**

## Verified upstream (do not modify)
- [PR #238](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/238): `docs/design/MORWEN_RIG_01_PROTOTYPE_SPEC.md`, a **PROPOSAL / BLOCKED_CANON_BINARY** for a 2D orthographic cutout rig. The director source binary was unavailable to that task. Target 48x64 frames and anchor (24,63) are Morwen prototype goals, not Fiona requirements.
- [PR #229](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/229): `tools/character-asset-studio/rig-integration/` defines `cas/rig-import/08`: four directions, rigPx/sheetPx, explicit joint IDs and parent graph, four ordered L0-L3 layers, sha256-pinned PNGs, explicit anchors, no mirroring; Morwen import template is **BLOCKED**.
- [PR #230](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/230): `anchor-rig-bridge/mappings/sheet_to_rig.json` has **DERIVED_CANDIDATE** joint positions; `characterFitStatus=BLOCKED`. Do not transfer Morwen joint coordinates to Fiona.

## Shared contracts, character-specific data
| Shared | Fiona-specific |
|---|---|
| Joint naming and parent topology from `cas/rig-import/08` | Joint positions measured from approved Fiona full-body art |
| Four views front/back/left/right and L0-L3 ordered layers | Hairstyle, dress/corset, ornaments, staff, accessory visibility |
| SHA-pinned input PNGs, anchors, alpha checks | Fiona master SHA, independent four-view art, anchors |
| Pose/time/stance/contact QA contract | Fiona walk timing and feet/weapon attachment |

## Safety gate
1. Preserve existing `tools/blender/fiona_candidate_rig.py` as a **standalone provisional scaffold**, not an adopted common rig. Its 20 bone IDs and Blender meter positions are not asserted to match Morwen's 2D `cas/rig-import/08` joints.
2. **Do not silently convert 2D pixel coordinates into Blender 3D meters.** A versioned adapter must explicitly map coordinate systems, parent IDs, side labels, and ground anchors.
3. Full-body Fiona reference and SHA-256 must be verified before measured joint coordinates, costume layers, and a production Blender mesh.
4. No edit to Morwen files, approved PNGs, registry, main, or published site.

## QA
- [x] Morwen prototype spec, import contract, and derived bridge located and read.
- [x] Existing Fiona scaffold classified as **not common-rig compatible**.
- [ ] Full-body Fiona approved master SHA and four-view visual verification.
- [ ] Shared topology adapter and Blender execution tests.
- [ ] Physical-device visual QA and director adoption.
