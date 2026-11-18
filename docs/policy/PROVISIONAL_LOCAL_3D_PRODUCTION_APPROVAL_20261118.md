# TWO｜仮ローカル座標による独立3D制作の承認（2026-11-18）

Status: DIRECTOR-APPROVED production scope. This is a later, narrowly scoped exception to the former global NO-GO for new geometry. It does not approve a canonical world metric or main merge.

## Director decision
- Character and map teams may **resume independent, non-destructive 3D asset production now**, using provisional asset-local coordinate systems. The director explicitly permits adjusting real-world scale later as overall game development progresses.
- Do not block standalone sculpting, modular buildings, rocks, cliff sections, materials, UVs, rigs, animations, or renders merely because world-wide metric scale and map anchors are unapproved.
- Do not infer a canonical metre scale from concept art, candidate D, HOME/BUILD kit values or a Blender scene. Provisional local dimensions are technical authoring choices only; label them `PROVISIONAL` and retain transforms and provenance for later revision.

## Workstream boundaries
- **CHARACTER / Morwen:** prioritize approved Layer 0 four-angle reference and the later visual-equivalence reference policy. New authored sculpt is first-choice method; unmodified CC0 base plus design sculpt is an alternative subject to license and independent QA. Preserve PR #407/#417/#419 as failed-method evidence. Do not retry failed cage, boundary interpolation or quad-patch methods without a documented structural method switch.
- **MAP / Windwaiting Cliff (風待ちの崖):** follow Art-Directed Hybrid World Production. Author major cliffs/bedrock/overhangs as sculpted or precise meshes; use heightfields only in appropriate gentle terrain, Geometry Nodes for scattering, and verified CC0 assets where suitable. Reuse provenance and lessons from PR #351/#353/#415/#416/#421; do not adopt failed models as finished assets.
- Separate branch/PR and ownership per workstream. Do not overwrite originals, merge main, delete legacy work, or publish without explicit approval.

## Required provisional asset interface
Each new asset must record:
1. source reference paths and actual SHA-256, approved/candidate status, applicable design decisions, license;
2. `coordinate_space: asset-local-provisional`, `unit_scale_status: UNAPPROVED`, up/forward axes, origin and ground/contact convention, versioned local bounds, transforms, producer commit, Blender version;
3. independent editable .blend master, external texture dependencies, export/GLB status, render PNGs and reproducible QA evidence;
4. any pending canonical anchor, world scale, camera, path/bridge/terrain attachment and consumer dependencies as `BLOCKED_FOR_INTEGRATION` (not guessed).

## Gate separation
- **Independent asset creation and local QA:** GO. G1 on reference identity and asset-local contract may be assessed; G2 art and local G3 technical tests must be performed on actual outputs, not inferred from CI. Never mark untested G2/G3 PASS.
- **Canonical world placement, WORLD↔ROUTE↔HOME↔BUILD↔ECO interfaces, traversal, scene integration and global metre-scale QA:** BLOCKED until separately agreed contracts and actual Blender integration tests.
- **G4 WebGL/Android:** NOT_RUN until actual game integration/performance testing. Final official adoption still requires G1–G4 PASS.
- Existing technical Blender 5.2.4 qualification on main is reusable; no need to repeat installation research.

## Production next action
Character and map owners should create actual independent high-quality assets and renders in their respective workstreams, with bounded scope, source locks and independent QA. Do not create more procedural placeholder geometry or repeat previous failed attempts. This approval removes only the provisional-world-scale blocker from standalone production.
