# LIND GEOLOGY / ROUTE — production handoff 01

Status: AUTHORIZED NON-DESTRUCTIVE WORK; IMPLEMENTATION NOT YET RUN. Base: PR #350 head 59b6eda768d480202b598c27f58229bbfc2d2543. Preserve PR #346 candidate D and failure history. This document is not an asset, render, or QA PASS.

## Shared contract and ownership
- WORLD owns cliff geological structure and terrain interfaces; ROUTE owns engineered road support, abutments and junctions. Never concurrently edit the same .blend or asset path.
- Read latest AGENTS.md, HANDOFF.md, Blender.md, official map source and SHA ledger before writing. If official metric/spatial approval unavailable, mark full G1 BLOCKED. Do not infer meters from concept art.
- Keep the two source branches/units isolated; WORLD publishes interface surfaces and anchor metadata, ROUTE consumes an immutable WORLD input SHA. No whole-scene append of ROUTE's contextual WORLD geometry.
- Reuse the PR #350 WORLD/ROUTE pipeline for Blender, render, hashes, cache and artifacts. No additional AI API or dependency without evidence of need.

## WORLD task: new geological construction method
1. Keep candidate D immutable. Replace the exhausted smooth heightfield/periodic rock-band *method*, not just its parameters.
2. Build a bounded high-fidelity coastal cliff sector with independently sculpted/joint-constrained fractured rock volumes, erosion breaks, credible grassy top, rock/soil transitions and weathered PBR material separation. Retain topological distinction between northwest ocean cliff and east river cliff.
3. Record geometry-generation script, Blender version, settings, seeds, input SHA, output SHA, licensing for external references and actual rendered PNGs (overview + close-up + gameplay-distance).
4. Technical checks: finite/manifold where appropriate, normals, no degenerate faces, material IDs, no unintended geometry intersections, reproducible saved .blend reopening. Art acceptance requires independent visual review against approved source at target display size.

## ROUTE task: engineered support and junctions
1. Start from candidate D as immutable measured reference; produce separate route support meshes and explicit bridge abutments, embankments, retaining walls where structurally needed.
2. Derive route profiles from actual deck/support geometry and shared junction surfaces, not a nominal +0.05 offset or a post-hoc floating ribbon.
3. Verify independently using actual evaluated triangles: center/edges plus triangle interiors, road-support gaps and continuity, bridge abutment alignment, junction overlap, slope, step heights and collision/nav feasibility. 1,557 previous samples are regression evidence, not full route acceptance.
4. Export actual Blender render PNGs at overview and junction close-up, .blend, machine-readable measurements and SHA ledger.

## Independent QA and gates
- QA must use separate scripts/reviewer, not producer self-assertions. Retain failed artifacts and cumulative same-method attempt counts; after two effective same-root/method failures, stop and redesign.
- G1 official canon/spatial: BLOCKED until reviewed; G2 final art: FAIL/NOT_RUN until independent image QA; G3 only tested subsets PASS; G4 runtime/Android NOT_RUN.
- On PASS of bounded structural QA, proceed only to previously approved deterministic follow-up. Do not auto-approve aesthetics, integrate production game, merge main, replace adopted assets, delete, or publish.
- Outputs: separate WORLD and ROUTE render thumbnails, blend, scripts, manifest SHA, qa.json, shortened failure log, change summary and Draft PR evidence.

## Execution priority
First make the bounded WORLD cliff sector and ROUTE bridge-junction sector in parallel; validate shared geometry interface before scaling to the entire village. HOME/ECO remain out of scope. If Codex cannot execute in this environment, this handoff remains queued and must not be represented as completed implementation.
