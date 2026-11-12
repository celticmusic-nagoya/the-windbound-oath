# FIONA-BLENDER-01 — Blender asset preparation (CANDIDATE)

Status: REFERENCE_PREPARATION / NOT_ADOPTED

## Canon source lock
- Current `AGENTS.md` and private `the-windbound-oath-handoff/reference/lore/` official v5.0 main + CANON_ADDENDUM + CANON_STATUS.
- Fiona: 18-year-old human; not an elf; green eyes, light chestnut long wavy hair, floral/leaf ornament; ivory, dark green and antique gold; linen blouse, leather corset, vine staff with green gem (existing field asset description).
- Preserve original PNG bytes and existing portrait adoption manifests; never promote experimental art.
- Existing field sprites: `docs/field/m9-hero-bench.md` describes 512x640, anchor (256,600), 4-direction frames. This is a 2D output spec, NOT a 3D model scale.

## Blender preparation
1. Identify *exact* currently adopted illustration and registry entries, record source paths and SHA-256 before using visual references.
2. Produce four orthographic A-pose views (front/back/left/right) with consistent proportions; do not invent hidden-side ornaments or alter approved asymmetry.
3. Separate head, hair front/back, torso, upper/lower arms, hands, legs, footwear, corset, decorative elements, staff and gem into Blender objects.
4. Draft armature with pelvis/spine/chest/neck/head, bilateral clavicle/arm/forearm/hand, thigh/shin/foot/toe and optional hair bones; confirm placements against adopted views before rigging.
5. Candidate-only output: reference PNGs, source provenance manifest, rig notes, QA report. No runtime references, production PNG replacement, site publication or main merge.

## QA gates
- [ ] Exact adopted source paths and hashes verified
- [ ] Four-view proportions and clothing details visually compared with source
- [ ] Alpha/transparency and shared origin checked
- [ ] No modifications to adopted images, registry, gameplay, save or website

Unverified reference details remain BLOCKED, not guessed.
