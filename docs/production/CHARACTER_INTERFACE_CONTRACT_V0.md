# CHARACTER-INTERFACE-01 — Shared immutable contract (v0, pending canon)

Status: DRAFT / UNLOCKED / NOT_FOR_MODELING. Source: PR #332 production and handoff specifications; main AGENTS.md; current main canon references. All unspecified numeric values are null, never guessed.

## Scope
Target Morwen first. Fiona and Aidan require independent per-character manifests. Interface changes require a reviewed interface PR; no producer silently changes the contract.

## Verified sources
- Main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md checked 2026-11-16.
- Morwen design master: user attachment 7374.png, actual JPEG 1536x1024, SHA-256 47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638. Binary NOT in public GitHub; visual G1 BLOCKED.
- docs/design/MORWEN_V561_CANONICAL_20261108.md and data/morwen-design-canonical.json: DESIGN_REFERENCE_APPROVED, production sprite NOT APPROVED.
- Private lore main CANON_STATUS.md and CANON_ADDENDUM.md accessible; full private bible and latest image binary still require exact verification before lock.
- Current eyelid/lash experiment: Draft PR #327; 09P surface collision FAIL; 09Q diagnosis pending. Do not alter its assets or reset its retry ledger.

## Required interface values
| Field | Status | Value or action |
|---|---|---|
| character_id | CONFIRMED | morwen |
| design reference SHA | CONFIRMED_METADATA_ONLY | 47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638 |
| head/body ratio | PROVISIONAL | 2.8 heads is field presentation target, not measured 3D seam geometry |
| world unit and origin | BLOCKED | derive from approved Layer 0 blend, verify actual object transforms |
| coordinate axes / 4 directions | BLOCKED | derive from source rig and game camera, no axis guessing |
| camera / framing | BLOCKED | derive from current field renderer |
| neutral pose | BLOCKED | inspect approved rig/Layer 0 |
| neck seam coordinates | BLOCKED | measure same coordinate frame on head and torso |
| shoulder / waist seams | BLOCKED | measure approved Layer 0 |
| rig bone names / bind transforms | BLOCKED | read actual rig and check parent hierarchy |
| face controls | BLOCKED | inspect current approved controls |
| UV and material slot IDs | BLOCKED | inventory approved Blender data |
| costume layer and occlusion masks | PARTIAL | visual inventory documented; exact mask IDs unverified |
| equipment slot IDs | BLOCKED | inspect existing modular sprite and headgear specifications |
| display dimensions | PROVISIONAL | native 48px and 96px previews required by PR #332; also verify actual 32/40/48px game sizes |
| full-body alpha export | REQUIRED | PNG RGBA with measured alpha, not checkerboard pixels |
| Blender version | VERIFY_PER_JOB | pin and log exact runtime version |
| deterministic seed | REQUIRED | record explicit seed or state no randomness |
| reference license | REQUIRED | document origin and rights, no unknown external asset insertion |

## Contract lock gate
LOCKED only after every BLOCKED field needed by FACE/BODY/COSTUME is measured from the same accepted source and reviewed. An unverified number must not become an interface default. Until then, branches may create source inventories, manifests, tests and designs but NOT claim integrated compatible models.

## G1–G4
G1 source-image/canon comparison BLOCKED; G2 independent artistic review NOT_RUN; G3 source/mesh/interface technical checks NOT_RUN; G4 full-character/game/Android NOT_RUN. GitHub CI PASS cannot certify G2/G4.

## Isolation
FACE owns head/face/hair/expression candidate collections; BODY owns torso/limbs/rig candidate collections; COSTUME owns clothes/accessories/occlusion candidate collections. INTEGRATION consumes frozen reviewed outputs only. Each branch writes assets/candidates/<task_id>/<candidate_id>, tools/character_blender/, docs/qa/. No canonical overwrite, main merge, publication or destructive deletion.

## Source audit 2026-11-16 — critical conflict
- docs/design/MORWEN_LAYER0_REFERENCE_REGISTRY.json (on PR #326 branch) records Layer 0 sheet SHA 7e122ceb205e502aad49dfa32ac463818e30a3da4d4bd43951f9263bcb08a150, dimensions 1536x1024, approximate 163 cm and 7.5 heads; these are **unverified source metadata**, not the field sprite's 2.8-head target.
- tools/blender/production_mesh_08/layer0_reference_manifest.json lists four source panels 7809/7807/7810/7808 with hashes, but explicitly says their image bytes are not in GitHub.
- The reference registry specifies character-left +X, right -X; docs/design/MORWEN_LAYER0_PRODUCTION_GATE.md states local +X is character-right. **AXIS_CONFLICT: BLOCKED** until checked against the accepted image, actual rig, and rendering transforms. Neither statement is silently promoted.
- Existing CONTACT_CAGE_DISABLED_08.blend is a *candidate diagnostic*, not a verified accepted Layer 0 master. Its mesh transforms can be measured for a provisional geometry interface, not promoted to canonical scale or seam.
- docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json labels pixel landmarks approximate and not art-approved; barefoot and booted heights must not be equated.
- The face/body/costume branches remain preproduction; no independently running Claude or Codex session was launched.
