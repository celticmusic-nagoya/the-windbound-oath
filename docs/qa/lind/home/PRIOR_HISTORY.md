# LIND-HOME-01 — prior history import (Aidan's house)

Status: HISTORY IMPORT (read-only). Sources read on 2026-11-16 via `gh api repos/celticmusic-nagoya/the-windbound-oath/contents/<path>?ref=<branch>` (REST; no checkout, no push).
Counters below are **not reset**. They are carried forward into `docs/qa/lind/home/attempt-ledger.json`.

## PRs read
| PR | Branch (head SHA) | What it holds | State |
|---|---|---|---|
| #307 | `feature/rilde-roof-canon-bluegray-20261114` (`2e2e10e`) | `docs/design/FIELD_VISUAL_OVERHAUL_20261108.md`: Rilde roofs are **blue-gray stone-slate**, director-approved 2026-11-14, replaces the older red-brown roof text; base = approved Rilde daytime CG | open, unmerged |
| #309 | `feature/aidan-asset-prep-01` (`2f6f629`) | `AIDAN_ASSET_SOURCE_AUDIT.md`, `AIDAN_BLENDER_STRUCTURAL_AUDIT.md`, `AIDAN_PRODUCTION_READINESS.md`, `aidan_asset_ledger.json` (CC0 ledger, Poly Haven / ambientCG), `aidan_blender_config.json` (units m, Z-up, front = -Y, 27° ortho game camera, seed 1311), SHA lock | open |
| #311 | `feature/aidan-roof-geometry-01` (`c86b857`) | roof V1–V3, approved visual target record (V11, SHA `bafade8c…66a8`, image NOT in repo), exterior design candidate, render gate 01 | open |
| #323 | `feature/aidan-architecture-v3-01` (`1df2fa0`) | architecture v3 diagnostic, corner bond v2, dressed stone v1/v2, material variation, masonry audits | open |
| #329 | `feature/aidan-masonry-pbr-study-01` (`85efab4`) | masonry families F1–F7, CC0 scan import audit, hybrid production gate | open |
| #331 | `feature/aidan-masonry-art-02` (`028afde`) | F8 scan-carved coursed rubble corner, candidates A/B, cumulative ledger F1–F8 | open |
| #337 | `feature/map-vegetation-master-01` | vegetation work order (ECO lane relevance only) | open |

## Whole-house / roof methods that are stopped
| ID (this ledger) | Method | Evidence | Result | Why stopped |
|---|---|---|---|---|
| H-A | Legacy candidate A: 672 identical slate pieces, 60 identical chimney stones, no image PBR, ~38° camera | #309 structural audit; #311 render gate 01 | G2 FAIL | identical repeated primitives, no UV/PBR; "do not spend a third iteration" |
| H-B | Legacy candidate B: thatched roof | #311 render gate 01 | G1 FAIL | contradicts blue-gray slate canon (#307) |
| R-V1..V3 | Standalone roof, vertex-first slate rows (v1 flat bands, v2 uniform rectangles, v3 offset shapes) | #311 AIDAN_ROOF_V2/V3_RENDER_QA | 3x G2 FAIL (tech PASS) | tiles regular/repeated, ridge and verge not authored, dark unfinished gable substrate, no house body. Directive: stop superficial slate edge edits; build integrated whole-house cage |
| A-V3 | Architecture v3: uniform box massing + bevel/displacement | #323 AIDAN_V3_PRODUCTION_HANDOFF | G2 FAIL | "do not polish v3's uniform boxes into final art" |
| C-BOND-V2 | Corner bond v2: regular prisms + chips (1–4 mm wear, 7 mm bevel, 3 mm displacement) | #323 masonry G2 recovery design | G2 FAIL | chips/bevels do not change the prism silhouette |

## Masonry method families (imported from #331 cumulative ledger)
| ID | Family | Status | Root cause of failure |
|---|---|---|---|
| F1 | Boolean-chip rectangular blocks | **STOPPED** (G2 FAIL) | box silhouette; chips/bevels too small |
| F2 | Broad-plane horizontal rings (quoin_broadplane_v1, run 43781482098) | **STOPPED** (G2 FAIL) | same plan vertices on every ring → periodic belts; exposed backing |
| F3 | Faceted perturbed cubes (facet v2, run 43782248901) | **STOPPED** (G2 FAIL) | triangulation changes shading, not macro outline; fixed grid, unverified joints |
| F4 | Raw scan boulders clipped + arbitrary offsets (run 43786045981) | **STOPPED** (G2 FAIL, G3 FAIL 0.15 m float) | no coupled contact geometry; reads as piled rocks |
| F5 | Planar joint-first + independent silhouette rings (run 43786940632) | **STOPPED** (G2 FAIL) | ring scaling bevels bearing faces away from the shared plane |
| F6 | Shared-surface contact feasibility | TECHNICAL_BASELINE (not art) | — |
| F7 | Primitive blocks + exterior-only procedural noise relief (run 43789139055) | **STOPPED** (G2 FAIL) | noise cannot change a rectangular silhouette; flat caps |
| F8 | Scan-carved coursed rubble (CC0 scan window ∩ layout cell, exact Boolean; mortar = envelope − cells) | ACTIVE_CANDIDATE in #331 (not stopped; independent G2 NOT_RUN; self-G2 "not adoption level") | open defects: slab-like flat stones, quoins not larger than coursing, bright moss band; ~150k tris for one 2–3-course corner |

## Consequences for LIND-HOME-01
- F1, F2, F3, F4, F5, F7, H-A, H-B, R-V1..V3, A-V3, C-BOND-V2 are **not reused**.
- F8 is not stopped, but it is not scalable to a whole house on this machine (one corner = ~150k tris and exact Booleans per stone; whole house ≈ 1,000+ stones) and it carries three open self-G2 defects. LIND-HOME-01 therefore opens a **new family F9** (see `attempt-ledger.json`) instead of continuing F8, and does not count F9 results against F8.
- F9 causal difference (hypothesis, must be proven by renders): the macro outline of every stone is an authored, rounded, irregular **2D outline derived from a wall-plane snecked-rubble layout** (cells, jumpers that span two courses, pinning snecks), extruded perpendicular to the wall so beds/perpends stay shared planes by construction (fixes F5), with a crowned (pillowed) exposed face. Not a cube/ring/noise perturbation (F1/F2/F3/F7), not a scan placed at guessed offsets (F4), no per-stone Boolean (F8 cost).
- Roof: whole-house integrated framed roof (rafters, deck, wall plates, bargeboards, ridge saddles, flashing) with individually placed slates that tilt on the course below, per-slate chipped outlines and staggered bond — required by #311 next-phase note; this is not a standalone roof patch.
- Inherited unresolved gates: exact house dimensions (G1 BLOCKED in all prior PRs); V11 visual target image not in any repo (SHA only); independent G2 for any Aidan masonry still NOT_RUN.
