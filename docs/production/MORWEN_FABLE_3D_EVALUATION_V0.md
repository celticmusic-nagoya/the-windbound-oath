# MORWEN — Fable-assisted 3D production evaluation v0
Status: PROPOSED / NON-DESTRUCTIVE / NOT_EXECUTED

## Goal
Evaluate whether Claude Fable 5.2-assisted Blender cleanup/rigging improves production quality, reproducibility and total work relative to the current Blender Python pipeline. This document does not authorize canonical asset replacement, paid service use, main merge, or publication.

## Evidence and limitations
- Public workflow example: TripoAI JP, 2026-11-15, https://note.com/tripoaijp/n/nd35c915948a2 — Tripo generates textured base meshes; Claude Fable 5.2 orchestrates Blender cleanup, rigging/animation/rendering. Vendor-authored example, not a controlled benchmark for Morwen.
- Independent comparison: https://zenn.dev/okzaq/articles/claude-fable52-lowpoly-3d-asset — different assets, reported conditions/cost differences; not evidence of canon fidelity.
- Fable execution is NOT available/verified in this GitHub Actions environment. Do not claim agent work completed or provision paid accounts automatically.
- The official Morwen Layer 0 image binary is not currently available in the public repo. Its metadata alone is insufficient for visual G1 PASS.
- Previous candidate metrics and seam diagnostics are exploratory; 7.5–8 heads is the director-approved target, not yet measured and certified on a finished model.

## Protected inputs
- Existing canonical character art, colors, asymmetric costume, hair, accessories, and approved references: immutable.
- Existing Morwen experimental Blender candidate (PR #326) and diagnostic artifacts: immutable.
- Current FACE/BODY/COSTUME parallel work packages PR #334/#335/#336: preserve; integration requires reviewed contract.

## Stage A — prerequisite verification (read-only)
1. Resolve actual Fable 5.2 product access, model availability, supported Blender control method (Claude Code/MCP/script), account permissions and pricing. User authorizes connection if required.
2. Acquire approved Morwen Layer 0 original image and check actual bytes against canonical SHA; compare exact front/side/back directions. Missing source => G1 BLOCKED.
3. Resolve left/right X handedness conflict between reference registry and production gate; never guess.
4. Record Blender, Fable, Tripo/fal versions, seeds, licensing, prompts, exact input hashes, and permitted external upload policy.

## Stage B — one bounded quality-first comparison (no production overwrite)
- Baseline A: existing candidate, frozen SHA and reference renders.
- Candidate B: Fable-assisted Blender processing of a **copy**, using the same approved reference and camera/lighting settings. Fable handles scene analysis, organization, rig checks and render orchestration; do not use primitives as a production-quality substitute for an organic character.
- Optional Candidate C: purpose-built 3D generation (Tripo/fal) only after rights/privacy/cost approval; preserve unmodified generated source and export logs.
- Compare: canonical silhouette, 7.5–8 head target, face and asymmetry, neck/shoulder/waist seams, topology/UV/material/skin weights, animation deformation, Android target performance, reproducibility and time/cost.
- Quantitative measurements do not replace independent visual G2 QA. If source art is missing, record BLOCKED instead of PASS.

## QA and decision
G1 canon/axes, G2 visual quality, G3 mesh/rig/UV/materials/render, G4 game-scale/performance/Android. All four PASS required for production adoption. Stop same-root retries after two meaningful failures and change approach. Log actual tool runs and artifacts. No main merge, publishing or original replacement without explicit approval.

## Immediate action
Wait for verified Fable access and approved source image. Meanwhile continue read-only Blender QA in the existing Draft PR; do not claim the Fable trial has run.
