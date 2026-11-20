# TWO | High-end 3D technology re-assessment and production pipeline

**Director-approved cross-asset production policy | 2026-11-20 | main-distributed guidance, not approval of individual models, tools or assets.** Applies to ChatGPT, Codex, Claude, Gemini, automation and future sessions. Read current main AGENTS.md, docs/production/SESSION_CONTINUITY_INDEX.md, current private canon and asset-specific approved references first. Supersedes *categorical technology rejection based solely on a prior failed candidate*; does not undo valid evidence of an individual failed result or waive security, cost, licensing, G1–G4 or merge gates.

## A. Failure attribution / re-evaluation (MANDATORY)

For each historically failed technique, classify separately: (1) reference/blueprint incomplete, (2) incorrect source asset or license, (3) missing workstation/Blender/add-on capability, (4) bad parameterization/algorithm, (5) implementation defect, (6) actual fundamental unsuitability, (7) unresolved. A failed result is **not** proof that the whole tool, source category or approach is intrinsically unusable. Retain old failure logs and exact method family; only retest with a *documented causal change*, valid inputs, measurable acceptance criteria, capped retries and a stop condition. Do not turn this policy into endless technology experiments.

Before any production tool or base is adopted: verify canonical source and SHA/provenance; define target silhouette, geometry, materials, camera, animation, runtime size, platform and deliverables; produce a sufficiently detailed blueprint/technical contract; identify dependency/license/cost; execute a bounded real asset test; compare against a controlled baseline; obtain independent art and technical QA; then record APPROVED_FOR_PRODUCTION only if justified. Status vocabulary: RESEARCHED / CANDIDATE / TEST_READY / TESTED_PASS / TESTED_FAIL / BLOCKED / IN_PRODUCTION; individual G1–G4 remain separate.

## B. Asset-specific priority matrix

| Workstream | Tools / method candidates | Production hypothesis and evidence gate | Status as of policy adoption |
| --- | --- | --- | --- |
| Morwen face/body | VRoid Studio / VRM anime-styled base, newly authored stylized sculpt, CC0 realistic base, Blender multires/sculpt/retopo | Follow [blueprint-first Morwen policy](MORWEN_BLUEPRINT_FIRST_BASE_SELECTION_20261120.md): measured official Layer 0 four views, registered cameras/landmarks, matched three-way *editable mesh* comparison and independent G2. Previous VRoid-based failures do **not** reject VRoid categorically. | CANDIDATE; no winning base approved |
| Morwen hair/costume | HairHarpy 2.0, Blender curves/mesh/sculpt, authored garment thickness/UV and PBR/NPR | Verify publisher hash, source-available redistribution terms, Vulkan GUI, Blender loopback bridge and real mesh export; compare strand/clump silhouettes in four views; retain original scene. HairHarpy not mandatory for Blender head work. | RESEARCHED; GUI/export NOT_RUN |
| Character rig/motion | Cascadeur, Mesh2Motion, Blender armature/IK/constraints, VRM expression/LookAt/SpringBone | Test rig map, root motion, foot contact, weight/Shape Key retention, walk/attack cycles, GLB import/export and in-game animation. Review license, version, free-tier and whether CLI/headless is available. No claim that tool supports unattended Actions without proof. | RESEARCHED / candidate, runtime test NOT_RUN |
| Windwaiting Cliff C10 | CG Painter, mPainter, Blender texture paint, procedural PBR and CC0 scanned rock materials | Freeze approved geometry/cameras/lighting before A/B material comparison. Assess albedo, normal, roughness, crack/wetness masks, UV/texel density, seam artifacts, silhouette-independent visual gain and Android texture budget. Preserve existing C10 .blend and C9/C10 evidence. | CANDIDATE; plugin integration NOT_RUN |
| Bedrock / Irish stone architecture | Spirula Studio, photogrammetry, lawful CC0 scans, sculpt + retopo + normal/displacement bake | Compare actual scan geometry, provenance, scale, scan holes/occlusion, irregular stone contact and hand-authored silhouette. Scan is **reference/high-poly input**, not automatically a final walkable mesh. Test export format, GPU requirements, license and offline feasibility. | RESEARCHED; verified integration NOT_RUN |
| Shared build environment | Blender 5.2.4 verified baseline, Blender 5.3.0 isolated authoring, GitHub Actions Cycles CPU, asset library/Geometry Nodes, source and output SHA cache | Reuse successful 5.3 smoke and Layer 0 reference tests (Actions 44553193163, 44554802279); do not rerun identical inputs. Actual asset save/reopen, multiple-angle render, geometry QA, export/import and WebGL/Android performance still separate. Do not globally replace 5.2.4 originals. | 5.3 isolated smoke/reference TESTED_PASS; production integration partial |

**Existing owning work:** Morwen Draft PR #427 (and relevant older Morwen PRs), cliff Draft PR #421, Blender shared baseline PR #423 (merged), Morwen blueprint policy PR #430 (merged). Verify live ownership/HEAD and branch contents before touching; preserve existing PRs and do not merge their unfinished assets with this policy. Check existing material/scan/Actions work before initiating new tests.

## C. High-end art direction translated into actionable checks

The quality bar is informed by *Genshin Impact*, *Arknights: Endfield*, *The Legend of Zelda*, *Neverness to Everness (NTE)* and *NIKKE* as visual/production references, **not** a claim of their internal pipelines or permission to copy identifiable designs. Independently validate:

1. **Stylized characters:** strong front/three-quarter silhouettes; consistent eyes, face planes and hair volumes; deliberate color/material hierarchy; expressive deformation; clean topology and weights; readable outlines and lighting at actual game size.
2. **World:** authored large-scale cliff/architecture silhouette, geological strata and fracture logic, convincing rock contact, nonrepeating materials, vegetation/ecosystem placement, water/shoreline, depth/atmosphere and traversal clearance. Heightfields for suitable soft terrain only; high-relief cliffs require sculpt/precision mesh. Geometry Nodes for controlled scatter, not a substitute for art direction.
3. **Material pipeline:** high-poly sculpt/scan -> retopo/UV -> baked normal/AO/displacement where appropriate -> PBR textures -> art-directed stylization/NPR -> identical-lighting multi-angle comparison. Blender manual confirms multires sculpt and high-to-low bake; verify tangent-space normals and engine-specific shader behavior rather than assuming Blender parity.
4. **Animation:** reusable rig contract, deformation and foot-contact review, retargeting checks, readable anticipation/impact/recovery, combat animation timing, root motion and camera/collision coordination.
5. **Runtime:** retain editable high-resolution source separately from optimized GLB; evaluate triangle counts, draw calls, material slots, texture memory, LOD/culling, shader complexity, frame time and Android memory with measured results. Commercial-grade still renders do not establish G4.

## D. Mandatory blueprint / implementation / QA loop

- **Gate 0:** verify latest main, private canon, existing PR/branch/HEAD, approved reference, SHA and known failure families. Identify source image vs design-equivalent image; keep provenance. If one reference is blocked, progress independently verifiable subassemblies.
- **Gate 1:** blueprint: registered orthographic/three-quarter views, landmark coordinate table and confidence, provisional axis/scale, geometry topology and UV plan, material masks and palette, intended camera/light, final display size, performance budget and exact file outputs. Label estimated geometry, avoid inventing inaccessible vertices from 2D drawings.
- **Gate 2:** produce **real editable** .blend and actual PNG comparison; use controlled matched baselines for alternatives. Save source, dependencies, output hashes, camera/lighting metadata, mesh counts, software versions and licensing.
- **Gate 3:** independent G1/G2/G3 checks. Do not repair the same root-cause method more than allowed by causal retry policy; switch technique with documented rationale. G4 requires real in-game WebGL/Android evidence, not Blender-only renders.
- **Gate 4:** approved independent modules may proceed in parallel. Record owner, branch, inputs/outputs/SHA, QA status, blockers, next task, stop condition. No duplicate PR or Actions storms. No paid APIs, unapproved binary execution, destructive deletion, canon overwrite, main asset merge or public release without their specific approvals.

## E. Source/rights and test environment reference

- Blender 5.3 manual multires and bake: https://docs.blender.org/manual/en/5.3/modeling/modifiers/generate/multiresolution.html
- Blender Asset Browser: https://docs.blender.org/manual/en/5.3/editors/asset_browser.html
- HairHarpy upstream source and explicit source-available/unsigned warning: https://github.com/Rackta/HairHarpy ; https://github.com/Rackta/HairHarpy/blob/main/TRUST.md
- VRoid Studio: https://vroid.com/studio ; VRM: https://vrm.dev/
- Cascadeur: https://cascadeur.com/ ; Mesh2Motion: https://www.mesh2motion.org/ (verify current official identity/terms before download)
- CG Painter: https://3dnchu.com/archives/cg-painter-alpha-0-4/ ; Spirula Studio: https://3dnchu.com/archives/spirula-studio/ ; mPainter: validate vendor, Blender compatibility and license before installation.
- Khronos glTF: https://www.khronos.org/gltf/ ; Blender Studio stylized workflow: https://studio.blender.org/training/stylized-character-workflow/
- 3dnchu category for ongoing research: https://3dnchu.com/archives/category/software_tool/3d-animation-software/ ; third-party article is a lead, not proof of capability.

**Status of this policy:** research synthesis and mandatory decision framework only. Does not assert any new plugin installation, asset render, independent art PASS or game integration. Next executable production work remains in the owning Morwen/cliff PRs after reference and blueprint checks.
