# High-quality rendering: Claude / Codex handoff (2026-11-16)

## Scope and safety
Use Claude or Codex **only when their review or code contribution has a concrete quality or engineering advantage**. Neither assistant is a replacement for Blender's actual rendered frames, human art review, or Android game QA. This document is a handoff, **not proof an external AI was invoked**. No paid API calls, secrets, third-party image uploads, main merges, publication, or destructive cleanup are authorized by this file.

Current Morwen evidence lives in Draft PR #327, branch `feature/morwen-eyelid-09-lash-architecture` (stacked on #326). Do not treat that unmerged branch as main. Actual Blender run 43787429549 found 09B four cage triangle pairs, 09D five, both on left L00 faces 0/1 and cage triangles 938/940. Read-only diagnosis run 43787661277 should be checked for the latest evidence; do not infer a pass from a smoke-test success. G1 BLOCKED, G2 NOT_RUN, G3 FAIL, G4 NOT_RUN.

## Responsibility split
| Agent | Permitted work | Required evidence |
|---|---|---|
| ChatGPT / integrator | Canonical hierarchy, requirements, GitHub PR review, independent QA, final gate reporting | SHA, change list, CI and image evidence |
| Codex | Blender Python scripts, geometry/BVH collision algorithms, test harness, GitHub Actions, deterministic build | Separate feature branch + Draft PR, reproducible commands, tests and input hashes |
| Claude | Design critique, structural alternatives, silhouette and surface attachment review, render contact-sheet inspection when images are actually supplied | Specific annotated issues tied to source frames; no inferred visual PASS |
| Blender in GitHub Actions | Run pinned scripts, produce 4-direction renders and QA JSON, upload artifacts | Actual execution logs, image files, pinned runtime, SHA, artifact link |
| Director / authorized reviewer | Approve visual quality and canonical changes | Explicit decision |

No Claude/Codex connector or API is configured by this document. A user may delegate tasks via the corresponding service, or a separately authorized GitHub integration may run them. Never claim delegation occurred based on a prompt file alone.

## Render acceptance gates
1. G1: verify canonical 4-view references, asset hashes, dimensions, asymmetry and current approved design; missing originals => BLOCKED.
2. G2: inspect 4 directions at native gameplay pixel size and enlarged size; hair/hat/flower, left-right differences, clothing, eyelids, eye shape, materials, silhouette, lighting, no intersecting geometry.
3. G3: Blender model and render scripts reproducible, no collision in closed/half-open/open lid poses, valid alpha, normals, UV/material, consistent camera, same seed; explicitly audit NumPy import errors seen in bpy 5.3.0 logs.
4. G4: Android actual in-game display, animation continuity, performance and regression to existing assets.

No PASS from CI alone. An output with no real Blender render is NOT_RUN for rendering QA.

## Codex task handoff (next)
Read actual 09E root topology JSON from CI artifact and the current code before editing. Produce a **read-only** 09F diagnostic and a topology-aware root ribbon proposal, not another scalar offset tweak. Include cage triangle adjacency, actual winding, signed-side limitations, and full triangle-pair overlap. If the cause is uncertain, stop at report. Preserve official blend and refs. Work on a dedicated branch and Draft PR. Run tests in GitHub Actions. Do not merge.

## Claude task handoff (next)
Review the 09E measured report and **actual** front/side/oblique render images when available. Identify a high-quality eyelash-root construction and whether it matches the official Morwen design. If images or canonical references are absent, mark G1/G2 BLOCKED/NOT_RUN, not PASS. Provide specific, testable art corrections and avoid primitive-only placeholder geometry.

## Handoff checklist
- Repository / exact commit SHA and PR
- Canonical reference paths and their verified hashes, or BLOCKED
- Input model SHA and Blender version / wheel hash
- Blender scripts, random seed, command and output paths
- 4-direction PNGs and contact sheet at gameplay display size
- Collision QA JSON for each eyelid pose and material/alpha checks
- Human visual QA notes and Android regression results
- Explicit PASS / FAIL / BLOCKED / NOT_RUN per gate

## Resource controls
GitHub-hosted runners are not assumed to have a GPU. Use CPU-capable Blender Eevee/Cycles only within runner time budget and cost limits, with a small approved render scope. GPU, external inference, paid Claude/Codex APIs and uploads of private/canonical references require separate approval and license review. Keep generated assets candidate-only until all four gates PASS and explicit adoption approval.
