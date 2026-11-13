# MAP-INTEGRATION-AUDIT-01 — Codex work packet

Status: ASSIGNED / NOT EXECUTED BY CODEX
Owner: Codex (manual/agent handoff; this document does not invoke Codex)
Baseline: current main AGENTS.md and docs/design/FIELD_VISUAL_OVERHAUL_20261108.md.

## Mission
Read-only inventory of the existing browser RPG field map implementation before importing Blender renders.

## Required work
1. Identify actual map source files, tile/world coordinates, draw order, camera, collision, navigation, object anchors, events and story triggers.
2. Verify 25–30 degree quarter-view policy, image projection and render framing; propose a testable transform from Blender scene units to game world units.
3. Inventory map-related regression tests, mobile display dimensions, texture memory/performance and Android browser constraints.
4. Identify exact integration seams and a reversible staged migration plan with SAVE compatibility and no changes to existing player movement or events.
5. Report verified facts with paths/line references, risks and unknowns. No code changes to gameplay in this task.
6. Draft PR containing audit documentation only. No canonical overwrite, merge, publishing or deployment.

## Exit criteria
G1 canon alignment / source verification; G2 visuals not evaluated; G3 technical integration contract proposed; G4 device QA NOT_RUN.
