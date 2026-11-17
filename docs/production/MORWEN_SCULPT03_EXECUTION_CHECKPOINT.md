# SCULPT03 executed checkpoint — partial local eyelid topology, UNAPPROVED

Task: resume Draft PR #417 from its unedited workspace. Character team only.
Base PR head: `33ecfc9eda77e888f597069c2ea257ec69cf0780`.
No map, architecture, game integration, canonical image, original blend, or historical failure record was changed.

## Actual deliverables

- [Editable partial candidate](../../assets/candidates/morwen-sculpt03/morwen_sculpt03_v01_UNAPPROVED.blend), SHA `a04decd5d2b87a86725550fb545b8b118125a07d7c1010f82aaa6aeb54df3353`.
- [Authored local geometry](../../tools/morwen_sculpt03/build_eyelid_prototype.py): two new corner-anchored lid surfaces, 48 vertices/32 quads per eye; diagnostic blink key. This is actual Blender mesh work executed in Blender 4.3.2, not a specification-only update, and **not completed full-face retopology or manual GUI sculpting**.
- [Review script](../../tools/morwen_sculpt03/review_eyelid_prototype.py): 6 color + 6 clay 768px views, 3 isolated blink samples, 2 control-wire views, reopen and limited technical evidence. Local renders: CPU Cycles, 16 samples, no denoiser, seed 0; intentionally diagnostic and still noisy, not beauty/final-quality output.
- [QA sheets](../qa/morwen-sculpt03/color_context_sheet.png), [clay](../qa/morwen-sculpt03/clay_context_sheet.png), [wire/blink](../qa/morwen-sculpt03/local_topology_and_blink_sheet.png), [64px comparison](../qa/morwen-sculpt03/comparison_64px.png), [128px comparison](../qa/morwen-sculpt03/comparison_128px.png).
- [Cumulative ledger](../qa/morwen-sculpt03/ATTEMPT_LEDGER_03.md). Prior art failures remain STOPPED. No paid generation, external mesh or new asset license was introduced.

## Startup/source verification

Current main AGENTS.md was read and compared: PR branch differs only by its added v1.1 policy header. Private canon main commit `af0d068f4055bf0b207ffa9e02127df8c258438d` was accessed; Bible, addenda and status checked for Morwen (18; academy affiliation). No private full text is copied into this repository. Five packed reference SHA values match the existing manifest. Full G1 is still blocked by unaccepted landmark registration, not by missing binary references.

Original SCULPT02 SHA remains `90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b`. Source meshes, old keys, cameras, hair and packed images are retained in the candidate. Open character PRs #399/#407/#417 were checked; environment PRs #368–416 remain outside scope. `docs/handoff/HANDOFF.md` exists (historical material distinguished from canon); no tracked `Blender.md` was found.

Blender 4.3.2 execution is available. No managed desktop mouse/keyboard tool is exposed in this session; no human/manual retopology pass is claimed or silently substituted. The scoped local prototype uses explicit authored mesh arrays rather than primitive generation. This does not unlock final-art acceptance.

## Technique research/provenance limits

The preserved anatomical source uses Blender CC0 Human Base Meshes (existing provenance). New local stations/connectivity are authored for this project. No third-party art/model was downloaded. Native Blender quad authoring preserves the editable scene; external remesh/AI generation would risk landmark drift, lose the source correspondence and require new provenance. Neither technique supplies an independent art PASS.

Attempted official references: [Blender retopology](https://docs.blender.org/manual/en/4.3/modeling/meshes/retopology.html), [shape keys](https://docs.blender.org/manual/en/4.3/animation/shape_keys/introduction.html), [3dnchu retopology index](https://3dnchu.com/?s=retopology). Web tool returned 402/unavailable; shell HTTP fallback returned proxy 403 for all three. These pages were **not successfully consulted**; do not treat the attempted citations as verified research or a license source. No paid fallback was used.

## Remaining work and gates

G1 BLOCKED: source/reference hashes verified; front/profile landmark and silhouette registration still requires review. G2 FAIL: detached eyelid overlay does not replace the realistic face or heavy hair. G3 INCOMPLETE: local topology/deformation screen passes its narrow checks, but socket-to-face integration, eyelid/eyeball collision, full facial UVs, actual closed-lid contact, rig and animation acceptance are untested. G4 NOT_RUN: no WebGL/Android integration or actual device testing.

Next concrete edit: redesign/connect the facial orbital/cheek/nose surface around accepted front/profile landmarks, pair the eyeball geometry with the new aperture, and independently check contact. Then replace the stopped hair family with scalp-rooted layered asymmetric locks. Clothes/equipment/material completion, final rig/animation, performance and device QA remain unfinished. This checkpoint does not waive any acceptance gate or label partial geometry as the completed SCULPT03.

The candidate remains on the designated Draft PR. No main merge, original replacement, formal adoption or public deployment.
