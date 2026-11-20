# MORWEN | Authored sculpt production handoff (2026-11-18)

Status: IN_PROGRESS / NO GEOMETRY PRODUCED YET / CANDIDATE ONLY
Owner: character production; branch: `feature/morwen-authored-sculpt-20261118`; base: main.
Scope: independently authored sculpt, not restoration of failed topology.

## Canonical locks
- Read current main AGENTS.md and docs/production/SESSION_CONTINUITY_INDEX.md before edits.
- Read private handoff main Bible, CANON_ADDENDUM.md, CANON_STATUS.md before lore-dependent changes.
- Primary art reference: approved Morwen Layer 0 four-view originals. Locate actual file paths, inspect images, record each actual SHA-256 and provenance BEFORE sculpting.
- Other images permitted ONLY after documented visual equivalence comparison, per docs/policy/MORWEN_VISUAL_EQUIVALENCE_REFERENCE_20261118.md.
- Historical v5.61 JPEG SHA-256: 47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638 (not proof of current Layer 0 file bytes).
- Keep approved asymmetry, short straight dark-purple bob and straight bangs, glasses, purple witch hat, uniform, knee-high socks and accessory placements where supported by official four-view design. Do not infer occluded details.

## Method switch
- PR #407 sculpt02: G2 FAIL; #417 local topology: G2 FAIL; #419 quad patch: G2/G3 FAIL.
- Do not reuse deformed cage, local vertex fairing or boundary-interpolated quad patches.
- Author new organic sculpt with separate face/hair/body/clothing/equipment; only use licensed CC0 base if proven more efficient and with documented provenance.
- No primitive-only stand-in should be represented as a finished character.

## Local interface
coordinate_space: asset-local-provisional
unit_scale_status: UNAPPROVED
axes: Blender Z-up; forward, origin, ground-contact, dimensions and transforms TO_BE_MEASURED_AND_RECORDED before committing .blend.
blender: 5.2.4 (shared runtime verified in main; new asset not yet run).
world integration: BLOCKED_FOR_INTEGRATION.

## Next executable production task
1. Inventory official Layer 0 four-view paths, fetch/inspect actual image pixels, compute SHA-256 and compare design landmarks.
2. Create a genuinely new editable Blender sculpt master of head/face/hair and body in provisional local coordinates. Preserve distinct objects.
3. Save .blend and front/back/left/right/3-quarter render PNG, viewport wireframes, mesh statistics and exact SHA-256 for outputs.
4. Independent art review G2 and technical G3 on the actual outputs, including face shape, hair silhouette, four-view identity and intersections. Stop same-cause same-method after two ineffective attempts and switch method structurally.
5. Later UV/PBR/rig/animation and WebGL/Android QA as separate gates.

## QA as of handoff
G1 BLOCKED pending actual Layer 0 image-file visual verification and hash inventory.
G2 NOT_RUN for new authored sculpt.
G3 NOT_RUN for new authored sculpt.
G4 NOT_RUN.
No .blend, render PNG, GLB, Actions run or independent QA has been produced by this branch yet.
No original replacement, main merge, deletion or publication authorized.
