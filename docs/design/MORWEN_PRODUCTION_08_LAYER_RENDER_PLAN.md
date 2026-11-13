# MORWEN-PRODUCTION-08 Layered Render Kit

Local deliverable: MORWEN_PRODUCTION_08_LAYER_RENDER_KIT.zip (source image hashes locked).

## Scope
- 4 cumulative render stages: Layer 0 body; Layer 1 inner and knee socks; Layer 2 uniform, skirt and boots; Layer 3 hat, cloak, book, satchel and right-leg garter.
- 4 orthographic cameras per stage: front, right, back, left.
- 16 PNG previews, .blend candidate, QA JSON **only after Blender execution**.
- Garter is **character right leg** (+X under front camera at -Y), screen right in front view and screen left in back view.
- Source references are unchanged and SHA-256 validated at script runtime.

## Verification
- Python syntax: PASS.
- Blender render: NOT_RUN (Blender unavailable locally).
- Artistic resemblance: NOT_VERIFIED; disconnected body topology and primitive accessory geometry are not approved art.
- No promotion to canonical, no main merge.

## Next quality gate
Run Blender on the ZIP; inspect 16 actual frames. Do not use technical preview geometry as final art. Move to reference-matched continuous head/body topology, face, hair, and accurately modeled clothing after this diagnostic render.
