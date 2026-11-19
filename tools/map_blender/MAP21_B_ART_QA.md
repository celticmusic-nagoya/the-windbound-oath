# MAP21-B independent render review
Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43325875301
Result: TECH PASS / ART FAIL / NOT CANON
Images: rilde_map21_field.png and rilde_map21_cliff.png inspected.
- Field: nearly flat ground, jagged pixel-like paths, box houses, river painted as flat straight rectangle, simplistic bridge.
- Cliff: straight shoreline and sea rectangle; no credible cliff silhouette, sunset framing or village-fire occlusion evidence.
- MAP21 JSON route connectivity is a graph check, not traversable terrain collision verification.
- SHA report produced; runtime untouched.
Root causes: camera composition exposes low-detail heightfield; roads assigned per polygon cause jagged edges; river/sea modeled as cubes rather than carved channel and coastline; houses placeholders.
Next step: MAP21-C structural camera-first greybox, smooth trail masks, continuous river/coast water surfaces, event-camera ray test and path clearance. Do not claim final art or canonical placement before independent checks.
