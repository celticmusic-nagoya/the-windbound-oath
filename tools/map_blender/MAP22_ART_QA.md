# MAP22 independent render QA
Run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43329837899
Artifact 13993713774, SHA256 archive de33c24170f136c0cc30a9159dde295c6fde246464bc3a084f5da2be75a49802
Reviewed: rilde_map22_field.png, rilde_map22_cliff.png (960x540).
Status: CI PASS, ART FAIL. No canon adoption.

## Field image
PASS: terrain-conforming material roads replace elevated tube roads; river visibly follows lower channel.
FAIL: jagged pixelated path edges from per-face material assignment; uniform low-detail green terrain; no village buildings, props or vegetation; bridge remains a flat rectangular slab; steep exposed terrain boundary by river.

## Cliff image
PASS: a broad blue sea plane is visible.
FAIL: sea is presented as a diagonal polygon ending at frame edge, with black empty background and no sky or natural horizon. The sunset scene, character sightlines, ridge fire occlusion and event staging are not demonstrated.

## Engineering follow-up
- Stop iterating with per-face material masks for roads. Use smooth shader masks or actual terrain-conforming flat mesh strips, with explicit junction triangulation.
- Rebuild coast as continuous cliff-to-water geometry, sky world and event-camera framing before decoration.
- Add original modular cottage/roof/stone wall/trees from canon-specific dimensions and palettes; do not import restricted third-party meshes.
- Create reproducible independent art QA, collision and occlusion checks. No merge, publication or runtime changes.

## Verification
[x] CI run completed success
[x] Field image inspected
[x] Cliff image inspected
[ ] Gameplay collision and occlusion (NOT_VERIFIED)
