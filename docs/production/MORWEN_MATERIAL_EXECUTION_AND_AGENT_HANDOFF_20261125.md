# Morwen — material execution plan and conditional agent handoff v1.1
Director instruction 2026-11-25. Candidate only. Current AGENTS/main supersede this snapshot. #427 owns native, #540 owns independent materials. No competing native writer. Layer 0 official four views control innerwear; clothed v3 controls exterior. No redesign or hidden detail inferred.

## 1. Acquisition checklist
Each source requires exact URL, license, technique (measured/procedural), source byte SHA, map names, color space, dimensions, physical repeat scale if documented, output SHA, acquisition date and independent comparison. No uncontrolled scraping or paid service. Movie costumes (including Harry Potter) are observation only: drape, wool weight, seams, lining. Do not reproduce proprietary images, insignia or costume pattern.
- Uniform wool: ambientCG Fabric085 (photometric stereo, actual archive receipt #540); compare Poly Haven poly_wool_herringbone (photo/processing credited, wool/polyester blend, CC0, source not acquired). Herringbone is a comparison, not proof of canonical weave.
- Shirt/lining: https://polyhaven.com/a/stretch_poplin (CC0, fine woven cotton, not acquired).
- Innerwear Layer 0 and elastic: https://polyhaven.com/a/cotton_jersey and https://polyhaven.com/a/bi_stretch (CC0; not acquired, choose only by matched appearance; do not infer fiber from art).
- Leather: ambientCG Leather037 acquired (actual source/NormalGL/Roughness verified).
- Fittings: ambientCG Metal048A acquired (procedural, not measured). Compare with measured brass before claiming physical brass. Gold thread separate from metallic fittings.
- Eyeglass glass and hair: authored physical shader tests, no arbitrary photos pasted; select licensed material if useful. Hair fiber orientation is strand-tangent based, not a photo painted over the face.
- Robe/cape: compare wool and lining drape using authorized reference only; preserve existing cape design. New alternate robe design outside this scope.
Sources: https://polyhaven.com/license ; https://ambientcg.com/view?id=Fabric085 ; https://polyhaven.com/a/poly_wool_herringbone ; https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html . Follow asset and API terms separately.

## 2. PBR starting points (trial ranges, NOT canonical measurements)
| module | roughness | metallic | additional |
|---|---:|---:|---|
| wool uniform/robe | 0.55–0.85 | 0 | measured normal, restrained sheen |
| shirt/lining | 0.45–0.75 | 0 | fine weave, distinct surface |
| Layer 0 cloth/elastic | 0.45–0.8 | 0 | original purple/gold motifs, separate elastic |
| gold-thread trim | 0.4–0.7 | 0 initially | compare sheen/metallic thread separately |
| fittings | 0.25–0.45 | 1 for exposed metal | prior .30 trial; no claim of final alloy |
| leather | 0.35–0.65 | 0 | measured roughness/normal; use verified map as baseline |
| glasses lens | 0.02–0.12 | 0 | IOR ~1.5, transmission trial 1 in offline renderer; test game-compatible alternative |
| frames | 0.25–0.55 | material-dependent | compare black/purple frame, preserve canon shape |
| hair | 0.3–0.55 | 0 | anisotropy trial 0.3–0.7, strand tangent, compare against VRoid native shading |
No unsupported VRoid or VRM shader property assumed; Blender/offline and game implementation separate; RGB base color sRGB, scalar maps linear, NormalGL tangent. Final values from matched render/actual native and runtime, not these estimates.

## 3. Ordered concrete execution
1. Uniform: actual grid import/reexport run45618046492 success artifact15023063410 (archive b8ee069f9ed359d2fc82d32cdfff348b7f28fe506a62706d7e85bfb4ec743ad0, CRC and 31/31 SHA). Four requested angles actually show front/profile/rear/profile. Grid wraps horizontally: front visible c2–5, facing right c1–4, rear c6–7/c0, facing left c5–7; columns are zero-based 128px bins and visible coverage is approximate. Bottom two rows visible. Current native skirt is stock symmetric shape; reference asymmetry/length/pleat geometry not solved by texture. Trial-only composition script tools/production_qa/morwen_skirt_uv_fit_trial.py generated 1024×512 PNG SHA20f7d59ca5668c9816a8681c44973ffd56a04b50e8fab7a28b09e5e350dae5f6, RGBA SHAcc42bb0faf2881a1e258389b99b48a959495fdb2bd062611326ed24bed4a13fd; exact alpha/reopen, mean wrap RGB difference1.0078125. Previous crop trial lost vertical stripes; corrected with a full 96×96 repeat. x[464,560), stripe center y480/495 provisional; dark rear substrate is diagnostic only. Next: reproduce exact candidate bytes on runner or authenticated input, volatile import, reexport exact pixel match, four-angle comparison; refine location and template shape before native save. D4 production mask not passed.
2. Gold trim and fittings: verify thread vs metal in identical lights, preserve reference pattern/width and protect unresolved regions.
3. Leather, straps and Layer 0 innerwear: use existing module v2, official Layer0 archive14602858760 four hashes verified. Measure visible contours and gold motifs; no generic redesign. Fit ordinary movement, clipping and coverage; separate stocks/elastic/metal. Collect photo-derived knit and poplin and validate maps.
4. Glasses: native fit/frame first, multi-angle eye visibility; later lens material and engine transparency test.
5. Hair: meaningful native edits and independent four-view comparison; HairHarpy escalation only under existing policy; tangent highlights, not invented anatomy. No premature VRM export.
6. Existing cape/robe: heavier woven cloth, lining, drape and edge QA; no copied costumes.
Each stage: D0–D4 per scope, then G1–G4 applicable. Native save unique checkpoint, reopen, actual views, independent QA. Only qualified VRM/Blender after native readiness. WebGL/Android compare camera distances, mip/aliasing, draw calls, alpha ordering and memory. Do not declare a complete asset from swatches or a green CI run.

## Conditional assistant handoffs — not dispatched
Codex is useful NOW for exact reproducibility and native integration mechanics; Claude is useful after actual material import for independent art comparison. Neither blocks ChatGPT.
### Codex — bounded technical task (coordinate with #427 owner)
Read latest main AGENTS/index/registry/rules, private canon and owner HEAD. Reproduce the trial from exact three input PNGs/receipt; the local PNG is not yet hosted. Prefer existing #540 source recipes/verified artifacts, no public binary or stock UV disclosure. Validate expected pixel SHA cc42bb0f..., correct any exact-byte reproducibility discrepancy with evidence, then prepare a single existing VRoid volatile import on isolated copy; verify current run/lease before dispatch, do not duplicate or mutate existing workflow while another agent owns it. Preserve diagnostic success predecessor. If unavailable, deliver script/tests and precise blocker. Output 4 actual screenshots, reexport pixel SHA, native input unchanged, root cause and exact run/commit. No canonical UV assignment, native save, main asset merge or formal adoption.
### Claude — independent art QA (only after actual material trial output exists)
Use exact official clothed images/Layer0 separately and same-camera trial views. Assess localized plaid placement, trim height/width, dark cloth readability, fabric softness and stylization; flag silhouette asymmetry/length and visible clipping separately from material. Compare front/left/right/back, close/mid/far. Rear obscured in official clothed reference remains unresolved. Return actionable region IDs, pixel observations/uncertainty and PASS/FAIL/HOLD per item; no self-approval, no new reference image, no native writes. For Layer0 later, review faithful garments and observed asymmetry, not alternate design. Do not duplicate Codex execution.
