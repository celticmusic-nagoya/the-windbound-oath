# Morwen full-3D production restart: quality-first execution contract
Status: PREPARATION ONLY — no new basemesh, sculpt, finished model, or render approved.
Branch: feature/morwen-fable-eval-01; Draft PR #339. Canonical reference set: assets/canonical/morwen/2026-11-16/MANIFEST.json.

## Prerequisites and order
1. **G0 source integrity**: run `python tools/qa/verify_morwen_production_readiness.py --output qa_output/morwen_readiness/canonical.json`. SHA/byte check all 5 files. Never modify canonical inputs.
2. **Basemesh provenance**: independently verify Blender Studio Human Base Meshes license and actual downloadable URL; existing candidate audit ZIP URL is unverified. Fetch to isolated temporary workspace only after URL and license verification; hash, CRC, inventory and import into Blender; assess actual eye socket/eyelid edge loops, shoulders, hips, knees, UV/retopo compatibility. Missing evidence => BLOCKED. Avoid pretending source inventory proves geometry suitability.
3. **Design and measurements**: full body 7.5–8.0 heads (working design target 7.75); measure actual skull top (hat excluded), chin, feet, major joints and asymmetry from approved source and approved design notes. Image pixel measurements must be reviewer-confirmed; don't infer from alpha bounds. Confirm anatomical right-leg garter, thigh-high socks, round glasses, shoulder crest, satchel, asymmetrical hat, bob haircut.
4. **Sculpt modular**: licensed anatomical human base, separate face, broad hair locks, hat, outfit, cloak, straps, accessories. Do not retry rejected ellipsoid/tube head, polar annulus/zipper eyelid/mouth methods. Distinct material IDs, naming, transforms, pivot and rig plan.
5. **Calibrated render**: neutral gray material diagnostic first, then PBR material review, orthographic front/back/left/right and three-quarter plus face/hands/boots close-ups. Record Blender/bpy version, render engine, view transform, exposure, samples, light power, camera projection/scale, deterministic seed, source/scene SHA. Render to new output folder; never overwrite approved images.
6. **Independent gates**: G1 canonical alignment, G2 visual sculpt/material/identity quality, G3 mesh/render/UV/rig/texture integrity, G4 WebGL/Android performance and game-size appearance. No automatic G2 PASS from CI success. Capture thumbnails and hashes in artifacts. Two failed attempts per root cause/method family then STOP/switch method.
7. **Game handoff**: only after G1–G3, export GLB with LOD/texture budget justified by measured Android performance, then G4. Canonical promotion, main merge, release require explicit approval.

## Available infrastructure
- `.github/workflows/morwen-production-readiness.yml` read-only canonical preflight on branch push; evidence retained 14 days.
- `tools/character_blender/build_morwen_reference_scene.py` existing four-view reference rig with hash check.
- `.github/workflows/morwen-basemesh-source-audit.yml` source ZIP audit **not confirmed executed**, URL must be verified.
- `.github/workflows/morwen-parallel-production-gates.yml` legacy candidate technical QA; its old head renderer must not be treated as approved final production.
- `tools/qa/create_render_contact_sheet.py` previews only, no automatic art approval.
- ChatGPT can fetch a known GitHub Actions run artifact and display actual PNGs in the current chat. Autonomous image posting to all chats is NOT implemented.

## Current truthful gate state
Canonical SHA check: NOT_RUN for new readiness workflow; G1 BLOCKED until new mesh matches canonical; G2 NOT_RUN on new mesh (legacy head FAIL); G3 NOT_RUN on new mesh; G4 NOT_RUN. Existing official references unchanged. No new basemesh or full-body render has been created.

## Next authorized non-destructive actions
Verify readiness Actions run and artifact; verify basemesh source and licensing, create separate working mesh candidate only if evidence permits, inspect actual geometry and produce measured full-body neutral turntable. If source or licensing cannot be verified, stop with BLOCKED and request no canon promotion.

## Verified official basemesh distribution evidence (2026-11-17)
- Blender official demo-files catalog lists **Human Base Meshes v1.4.1**, Blender Studio/community, **CC0**, compatible with Blender 4.2 LTS or newer: https://www.blender.org/download/demo-files/
- Official v1.4.1 download landing page confirms direct mirror URL: https://www.blender.org/download/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip/ ; direct ZIP: https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip
- Blender project's own CC0 provenance record identifies source authors, license and six named meshes, including `Body Female - Stylized` and `Body Female - Realistic`: https://projects.blender.org/blender/blender/commit/4c4293010c2e21122b54681cd22556b727efbb11
- **PASS**: source identity, public availability listing, version, CC0 rights. **NOT_RUN**: actual ZIP download, SHA/CRC, Blender import, topology, visual comparison and model adoption. The existing source-audit workflow URL matches the official mirror URL; do not replace it without evidence.
- Prioritize inspection of `GEO-body_female_stylized` and `GEO-body_female_realistic`, preserving source as immutable and deriving separate candidate only after geometry QA. The CC0 license of the mesh bundle does **not** extend to unrelated assets in the same demo-files catalog.
