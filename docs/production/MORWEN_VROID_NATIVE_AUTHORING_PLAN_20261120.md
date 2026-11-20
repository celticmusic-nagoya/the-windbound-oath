# Morwen native VRoid authoring plan
Director-approved workflow; candidate targets only. Owner PR #427. No native edits performed by this document.
References: existing layer0_landmarks_v1.json, precision blueprint handoff, main AGENTS and blueprint policy. Official images 384×1024; front crown/chin 162px, eye spacing 52px, hair hem spacing 129px, estimated shoulders 156px. Normalize to crown–chin: 0.321, 0.796, 0.963 respectively (shoulders estimated). Profile crown/chin vertical 161px; nose projects 22px beyond chin in right image and 25px in left. Do not infer exact hidden skull or 3D depth from these drawings.
## Native operation order
1. Reopen verified M01B .vroid (SHA 9223661904a2ec33155959d3286f678869ef0c24866d51365f663886aeeeefcf), save new checkpoint; no overwrite. If open fails preserve original.
2. Face > Face Sets baseline; individual Eyes Sets, Irises, Eyelid, Eyebrows, Eyeliner, Eyelashes, Nose, Mouth, Skin. Inspect Parameters labels/ranges in live version. Record initial values; adjust eye spacing toward 0.321 head-height, nose/profile and chin against both side views; reduce excessive roundness only where comparison shows it. Set iris purple using source sampled midtones, custom texture for iris details. Neutral expression first, expression editor later. Do not assume exact slider names or numeric values before inspection.
3. Hair > Edit Hairstyle: use base/back volume and procedural groups, freehand guides for asymmetric fringe, select/retouch/control points for hem and curves. Target frontal hem span 0.796 head-height; profile and rear nape landmarks constrain length. Select material per group; sample base/highlight separately from source, avoid flat recolor. Save custom hair item, inspect both sides and back, then hair bounce.
4. Body: inspect actual body parameter list, register crown/ground, compare full silhouette. Target shoulder ratio approximately 0.963; do not infer hidden body under uniform. Adjust head/body/limb proportions from measured silhouette, not a guessed height.
5. Clothing: choose closest editable template, adjust silhouette first, export template textures and author layered PNGs for purple fabric/gold trim; straps/buckles and unsupported 3D pieces deferred to Blender if necessary. Maintain asymmetry and mark unresolved parts. Save custom items separately.
6. In one editor session take baseline and meaningful face/hair/body/clothing checkpoints. Record observed parameter names, initial/final values, screenshots and source hashes. Save versioned native files; reopen and verify. Same framing, front/right/back/left/three-quarter. Compare silhouettes and landmark errors; no invented measurements, no export until native art review.
## Official VRoid documentation (consulted)
- Face categories and controls https://vroid.pixiv.help/hc/en-us/articles/4406164546969-How-to-edit-faces
- Numeric parameter editor https://vroid.pixiv.help/hc/en-us/articles/360012681033-About-Editors-Design-and-Texture-Tabs-Properties-Panel
- Hair groups/material/brush https://vroid.pixiv.help/hc/en-us/articles/900005678786-How-do-I-customize-hairstyles
- Hair retouch/control points https://vroid.pixiv.help/hc/en-us/articles/360012339194-Hair-Editor
- Texture import/export https://vroid.pixiv.help/hc/en-us/articles/4405430561817-How-to-use-the-Texture-Editor
- Reusable custom items https://vroid.pixiv.help/hc/en-us/articles/900005583186-How-to-Use-Custom-Items
Exact version-specific body/clothing slider names, palette samples and GUI coordinates remain NOT_VERIFIED. Native batch execution NOT_RUN. No G1–G4 approval.
