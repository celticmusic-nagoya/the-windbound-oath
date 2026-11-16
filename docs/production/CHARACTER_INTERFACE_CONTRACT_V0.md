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
| head/body ratio | DIRECTOR_APPROVED_TARGET | 7.5–8.0 heads for new anime-style 3D character models; exact per-character ratio must be matched to the accepted Layer 0 source, not invented |
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

## Director-approved proportion and style override — 2026-11-16
- New 3D character production uses **approximately 7.5–8 heads**, with high-quality anime-style modeling informed by Genshin Impact and Neverness to Everness (NTE). This replaces the 2.8-head target **for new 3D character models and their future in-game presentation**.
- Preserve the exact approved character identity, face, asymmetry, costume, equipment and Layer 0. Visual references are style/technique inspiration only; do not copy third-party character assets or designs.
- Legacy 2D field sprites, their sizes, animations and code remain untouched pending a separate approved migration. The earlier 2.8-head specifications are historical/legacy compatibility references, not the new 3D production target.
- Design the new character at production-quality 3D proportions; validate silhouette and face at actual future gameplay camera and resolution. 48px/96px legacy previews are diagnostic only and do not define the new 3D character's proportion.
- Target is a range, not proof of measured canon geometry. Exact height, head length, neck seam, shoulder and hip positions, bone names and axes remain BLOCKED until verified from accepted Layer 0 and rig.
- This later explicit director decision supersedes conflicting 2.8-head statements in the character work packages and the PR #332 draft **for new 3D modeling only**.

## Source audit 2026-11-16 — critical conflict
- docs/design/MORWEN_LAYER0_REFERENCE_REGISTRY.json (on PR #326 branch) records Layer 0 sheet SHA 7e122ceb205e502aad49dfa32ac463818e30a3da4d4bd43951f9263bcb08a150, dimensions 1536x1024, approximate 163 cm and 7.5 heads; these are **unverified source metadata**, not the field sprite's 2.8-head target.
- tools/blender/production_mesh_08/layer0_reference_manifest.json lists four source panels 7809/7807/7810/7808 with hashes, but explicitly says their image bytes are not in GitHub.
- The reference registry specifies character-left +X, right -X; docs/design/MORWEN_LAYER0_PRODUCTION_GATE.md states local +X is character-right. **AXIS_CONFLICT: BLOCKED** until checked against the accepted image, actual rig, and rendering transforms. Neither statement is silently promoted.
- Existing CONTACT_CAGE_DISABLED_08.blend is a *candidate diagnostic*, not a verified accepted Layer 0 master. Its mesh transforms can be measured for a provisional geometry interface, not promoted to canonical scale or seam.
- docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json labels pixel landmarks approximate and not art-approved; barefoot and booted heights must not be equated.
- The face/body/costume branches remain preproduction; no independently running Claude or Codex session was launched.
