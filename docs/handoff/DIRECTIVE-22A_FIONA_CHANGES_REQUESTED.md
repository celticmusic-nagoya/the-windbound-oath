# DIRECTIVE-22A — Fiona image review: CHANGES_REQUESTED

Image owner: Claude. Reviewer/integrator: Codex. Source baseline: PR93/main `72c83eef1e3fef1c474a51f84e98f1bb3b3fbe45`.

Received private handoff `handoff/fiona-brow-22a-claude-20261030` @ `5fa353243a1acc3b9376cb901f1c7361c0bce277`, `reports/DIRECTIVE-22A-20261030/`. Reviewed HANDOFF, all8inspection/cause plates, right/left before-after, display-scale comparison, existing-blink comparison,5PNG SHA,qa and script/parameters. No image regenerated or modified by Codex.

## Verdict: image subset FAIL / not integrated

The five new PNGs are source-consistent (SHA and alpha exact,402/294/232/669/563changed pixels), but the repair removes **pink floating eyelid creases**, while the reported double-BROWN-eyebrow shape remains clearly visible in **angry / sad / worried / relieved**. The normal upper brown stroke and expression-specific lower/angled brown stroke both remain in the after image. The supplied changed bounds begin atY254 or below; the normal upper brow aroundY240 is untouched.

[Claude supplied before/after, retained for review](../qa/evidence/directive-22a/claude_candidate_brow_comparison.png). This is comparison evidence, not an adopted portrait. Do not integrate the5files as a completed double-brow fix. Smile's pink-line cleanup looks cleaner, but that is not sufficient evidence that the requested brown-brow duplication is resolved. Reinspect all8 faces and distinguish hair strands, actual expression brow, old normal brow and eyelid creases.

## Source vs rendering

The current double shape exists in RAW static PNGs. [Runtime audit](../qa/evidence/directive-22a/runtime-brow-audit.json): all8state0canvases exactly match the source crop, withONEcanvas/portrait element, no eye overlays and no timer. Renderer code clears the canvas then paintsonebase; overlays occur only atstate>0. No duplicated renderer/base layer or timer cause was found. Do not fix this by rotating/scaling the portrait or changing the shared draw pipeline.

Initial static classification: angry/sad/worried/relieved clear right-brow duplication; normal/determined no clear duplication; smile/surprised need careful distinction of faint creases/hair. Left brow is largely hair-obscured. Claude's current hypothesis classifies smile but notsurprised for crease cleanup; the difference in diagnosis is precisely why the actual BROWN strokes must be checked before the next delivery.

## Requested next delivery

- Correct ONLY the unwanted duplicated/ghost eyebrow stroke, preserving the intended expression's brow and all eyes/iris/lash/lid/mouth/contour/hair/clothes/ornaments.
- Preserve approved originals and all144formal blink PNGs (120expression+24normal). New version filenames/folder only. No whole-body regeneration.
- Provide exact original/new SHA, changed-pixel count/bounds/mask, alpha/outside-mask invariance, native-scale brow closeups and phone-scale before/after for all affected faces.
- Check newstatic base through existingstates0–4. If changed pixels overlap opaque blink pixels, determine whether the newbase's correction remains compatible; do not silently regenerate or replace formally adopted blink PNGs. Report any unavoidable conflict for resolution.
- Current handoff notes a normal-derived eyelid line duringblink. Independent pixel inspection found no exact oldexpression-pixel restoration in its changed mask; do not claim that old bytes literally return. This does not resolve the separate, still-visible two-brown-stroke issue atstate0.

Next actor: Claude — deliver revised new-version PNGs and comparison evidence targeting the actual duplicate brown stroke. Codex will verify and add DEV comparison only after a corrected package passes image QA. No fabricated/placeholder replacement or user approval question is needed now.

Blink formal adoption is independently authorized to land first under22A. All existing PNGs/runtime remain unchanged in that adoption PR. Image integration remains pending a corrected delivery; final image adoption is user Android QA only.
