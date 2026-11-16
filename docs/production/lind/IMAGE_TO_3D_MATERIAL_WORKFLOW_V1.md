# IMAGE-TO-3D MATERIAL WORKFLOW v1.0 — Approved production-method option

**Status:** director-approved **method as one option**, not approval of any particular generated image, model, placement, material or final asset. **Production implementation / Blender render: NOT_RUN.** Non-destructive candidate-only process.

## Evidence / reference

Director-provided 235.54-second tutorial MP4 reviewed 2026-11-17 (1280×720, H.264, 60fps). Sampled frames show image-driven appearances of water, sky and a squid in a game scene. The source illustrates the benefit of image-based appearance, **not** evidence that the exact tutorial uses a particular engine, AI tool, texture projection technique, PBR workflow or UV implementation. This workflow below is a production design derived from the example, not a verbatim transcript. Do not redistribute the source video without rights.

## Responsibility split

- **Codex / IMAGE-PRODUCER:** use approved canonical images and licensed references to prepare **original candidate** material images, preferably tileable PBR base color, roughness, normal/height where physically justified, alpha/mask and emissive as appropriate. Save per-asset manifest (intended target, reference hashes, prompt/settings, seed/model/tool/version, license, dimensions, color space, output SHA256). No copying unlicensed reference imagery. Image generation availability is an external dependency: Codex must **not** claim to have generated images unless actual files are produced. If its environment cannot generate images, deliver a reproducible request/spec and mark generation BLOCKED.
- **Claude / MATERIAL-INTEGRATOR:** verify image SHA, dimensions, alpha and rights, build the underlying appropriate Blender geometry, UVs/UDIM or projection, material node graph, physically sensible roughness/normal/displacement, edge transitions and LOD/bake. Preserve native geometry for silhouette, support, shadow and collision. For water use independent current/flow controls, transparency/reflection, and gameplay-safe fallbacks. For sky use environment dome/HDRI or skydome appropriate to runtime, not pasted sky on terrain.
- **Independent QA:** another reviewer compares final saved blend and actual renders against official CG at close, mid and target gameplay scale, and checks tiling, seams, stretching, mirrored artifacts, alpha sorting, light response, performance and asset provenance. Technical CI alone cannot pass G2.

## Appropriate uses / not substitutes

| Target | Image contributes | Geometry remains essential |
|---|---|---|
| WORLD cliffs / talus | multi-scale albedo, roughness, rock joint/erosion detail, decals | unique sculpted rock silhouette, fractures, soil support, occlusion |
| ROUTE masonry | stone/mortar surface variation, masks, dirt, lichen | full-thickness irregular stones, corners, arch and abutment bond, structural contacts |
| HOME / BUILD | blue-gray slate color variation, wood grain, plaster, stone weathering | real overlapping slates/rafters, window/door depth, roof valleys, wall courses |
| ECO | leaf/grass alpha cards and atlas, bark, water surface detail | branches, grass clumps, bank edges, water mesh and current |
| Background sky | authored/licensed panorama or HDRI | correct lighting/environment and runtime implementation |

## Candidate pipeline (non-destructive)

1. **G1 input lock:** identify canonical references and actual SHA; define intended look and license. Missing original => BLOCKED. No unapproved scale or placement assumed.
2. **Image production:** Codex produces a small, explicitly bounded candidate set; save source/parameters/seed/tool, output PNG/EXR, hashes and rights in isolated directory. No endless low-quality variants.
3. **Asset handoff:** immutable manifest with source hash, map type, UV tiling intent, texture channels, linear/sRGB flags, target mesh ID, source license, ownership and QA status. No material without provenance.
4. **3D integration:** Claude verifies hashes and maps images onto **actual modeled geometry**; produce blend + 3 camera renders + 48/96px check and separate runtime-oriented preview where feasible.
5. **Independent G2/G3:** reject texture-only imitation of missing geometry, obvious repeats, artificial rectangular stone pattern, grass caps, pink stone, grey slate, UV seams, floating tiles or alpha artifacts. Save review keyed to exact output hashes.
6. **Stop rule:** two effective attempts failing same cause => stop family, root-cause analysis and switch method. Do not relabel a texture to reset attempts.
7. **Adoption:** G1–G4 PASS required for formal asset adoption; main merge/replacement/publication requires director approval. G4 remains NOT_RUN until actual browser/Android testing.

## First bounded evaluation

- **ROUTE:** one irregular, full-thickness masonry junction/abutment section; original stone and mortar texture set by Codex, Claude applies to uniquely modeled stone geometry. Compare with failed automatic-facing candidate in PR #351 using fixed camera and lighting.
- **WORLD:** one independently sculpted fractured cliff segment, texture set for exposed rock + soil transitions; compare against stopped pillar/grass-cap candidate at detail, overview and gameplay distance.
- **HOME/BUILD:** only after HOME contract v1.1 SHA is pinned and checked; one stone/slate material sample without changing approved assets. ECO can test one alpha foliage atlas separately.
- No village-wide propagation until a bounded art PASS and shared interface acceptance.

## Audit states at registration

G1 method compatibility: candidate process documented; exact reference provenance and canon alignment per material NOT_RUN. G2 actual image/material visual review NOT_RUN. G3 Blender material/runtime implementation NOT_RUN. G4 game/Android NOT_RUN. **No image was generated, pasted or rendered by registering this document.**

Ownership: WORLD/ROUTE Codex remains responsible for geometry work; this workflow's Codex image-production role must coordinate with that owner. Claude HOME/BUILD/ECO ownership remains unchanged. Avoid conflicting edits or silently substituting textures for geometry.
