# CHARACTER ↔ ENVIRONMENT integration contract — 2026-11-16

**Status:** CANDIDATE / NON-CANONICAL. Character-team companion to `docs/production/CHARACTER_ENVIRONMENT_SHARED_HANDOFF_20261116.md` on `feature/lind-agent-blender-handoff-01`. No main merge or asset adoption.

## Source authority and conflict ledger
1. Read current `main:AGENTS.md` and `main:docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` at each session. Later explicit director approvals and current private canon main/addenda prevail; do not copy private lore to public repository.
2. Main's `docs/design/MORWEN_V561_CANONICAL_20261108.md` identifies the v5.61 approved **design reference** JPEG/JFIF SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`; production sprite NOT_APPROVED. The binary was not present in the public repo when recorded.
3. Character branch `feature/morwen-fable-eval-01` contains a later five-file director-approved reference manifest `assets/canonical/morwen/2026-11-16/MANIFEST.json`; its JPEG sheet SHA-256 is `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b`. **Different bytes, not interchangeable.** The manifest states a newer approval; confirm its actual director approval provenance and visual/design precedence before G1 design-conformance PASS. Preserve both records. Reference-input hash verification is distinct from authority reconciliation.
4. The current private `the-windbound-oath-handoff/main/reference/lore/CANON_STATUS.md` was readable at this audit; check the latest official bible and addendum independently before lore-dependent edits. Aidan, Fiona and Morwen are 18. Do not copy map source SHA `abbb3997...` into character provenance.
5. `main:docs/design/FIELD_VISUAL_OVERHAUL_20261108.md` specifies **approximately 2.8-head field sprites**, whereas the later character branch proposes **7.5–8-head high-proportion 3D**. These are separate deliverables, not competing values for the same file. No automatic 3D-to-field scaling or production swap.

## Team ownership / Blender reproducibility
- CHARACTER owns reference manifests, character candidates, rigs, directional renders, sprites, animation and their QA. WORLD/HOME/BUILD/ECO own terrain/buildings/geography; INTEGRATION owns an adapter contract; independent QA owns art/runtime verdicts.
- Shared *process*: immutable inputs, SHA-256 before/after, script commit, Blender version and dependency wheel/hash, fixed seed or `not_applicable`, camera axes/projection, render engine/resolution/color management, licenses, output hashes, attempt ledger and G1–G4.
- **Do not silently unify executable versions**: map `Blender.md` pins Ubuntu 24.04 Blender 4.0.2; current Morwen CI pins `bpy==5.3.0` with wheel SHA `5850cd39369e4cd8c67ed067d39ec1e57426103ddc709436e13209b56665c6a0`. Record separately; cross-version parity NOT_RUN. A process contract is shared, not a forced binary upgrade.
- The frozen Morwen technical candidate is `candidate_source/assets/candidates/morwen-eyelid-08-contact/inspection/CONTACT_CAGE_DISABLED_08.blend` at source commit `bca7d1d4cfd4b5e8a4f6c03656e148ed8485370c`, expected SHA-256 `9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4`. This is **not an approved Morwen model**.
- Four-view technical script: `tools/character_blender/morwen_four_view_capture.py`, wired to `.github/workflows/morwen-parallel-production-gates.yml` on candidate branch. Its PNGs are **review inputs**, not certified G2.
- Existing Morwen eyelid polar annulus/zipper family has two recorded failures (folding/UV inversion); STOP that family. A corner-anchored curve-constrained quad method requires a distinct logged hypothesis, not a reset of the historical attempts. Keep mouth defects separate. Before any new sculpt or render, inspect current PRs and the cumulative ledger; do not rerun unchanged candidates as an attempted art fix.

## Proposed field adapter contract (NOT implemented)
Character export must declare:
- `character_id`, `asset_variant` (field sprite / high-proportion 3D / battle illustration), `direction` (front/back/facing_left/facing_right), `state` (idle/walk/transition), `frame_index`, `frame_duration_ms`.
- Source SHA and per-output SHA; `canvas_px`, `display_px`, `pixel_density`, `pivot_px`, `ground_contact_px`, `shadow_anchor_px`, `shadow_footprint_px`, `visual_bounds_px`, `collision_bounds_px`, `alpha_mode` and `outline_policy`. Every value must be measured/approved; no inferred production defaults.
- `projection_id`, `depth_sort_anchor`, `occlusion_layer_contract`, `ground_height_reference`, `performance_budget_ref` and `animation_source` (sprite frames vs CSS/JS secondary motion).
- Map side supplies actual approved projection and scale, occlusion/depth masks for bridges/cliffs, walkable/collision/nav data, ground and shadow layers, Android performance constraints. Until both sides approve, these are `BLOCKED_UNAPPROVED_INTERFACE`.
- Do not alter existing DOM pixel movement, JSON height/collision, SAVE restoration or character state machine until an adapter is tested on a feature flag. The latest field policy favors directional stills + secondary JS/CSS motion; historical 12-frame walk work is preserved as candidate/history, not silently promoted or deleted.
- Test facing and idle/walk transition, contact-foot stability, alpha/outline at 32/40/48px, 25–30° field perspective, bridge/cliff occlusion, shadow grounding, reduced motion, SAVE/CONTINUE, landscape Android and performance. G4 NOT_RUN until actual runtime/device evidence.

## QA state at this document revision
| Gate | Status | Reason |
|---|---|---|
| G1 | BLOCKED | Old main v5.61 sheet and later five-file reference have different SHA; design authority reconciliation pending. Per-file checksum checks do not resolve precedence. |
| G2 | NOT_RUN | No independent visual assessment of approved final 3D/4-direction field sprite. |
| G3 | PARTIAL | Earlier candidate rig and front-framing technical jobs succeeded in run 43852160333; four-view capture newly wired but current commit run/artifact not verified. |
| G4 | NOT_RUN | No field adapter, runtime or Android evidence. |

## Next non-destructive tasks
1. Inspect latest Morwen branch Actions runs and artifacts, validate four-view PNG hashes and source immutability; if no run, report NOT_RUN and use a permitted manual dispatch.
2. Reconcile reference precedence using explicit director approval evidence and actual original image SHA; until then, create no final-design PASS or canonical replacements.
3. Produce candidate-only field adapter schema/tests from measured runtime values; preserve game behavior and the map team's separate geometry/QA.
4. For future outputs, write machine-readable provenance manifest, production log, per-gate QA and cumulative method-family failure ledger. No main merge, publication, destructive cleanup or source overwrite.
