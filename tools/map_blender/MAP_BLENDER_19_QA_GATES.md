# MAP-BLENDER-19 — Terrain integration acceptance gates

MAP18 source: Actions #43248082447; `map18_report.json` reports 9/9 synthetic ray occlusion at ridge height 5. Visual review of `rilde_map18_preview.png` is FAIL: terrain terminates in a visibly thin overhanging edge; village buildings are still uniformly spaced; bridge is planar.

## Next implementation (do not alter MAP18 predecessor)
- Integrate ridge into a single continuous terrain surface with positive thickness, smooth foothill transitions, and no hovering mesh edges.
- Derive material from slope and world-space noise; avoid polygon checkerboarding.
- Preserve the 9/9 synthetic occlusion baseline but independently inspect canonical event camera frusta (not yet defined in code).
- Create map route graph and test bridge crossing and north-road connectivity before decorations.
- Render comparison at field 27-degree view and at sunset cliff event camera.
- Art QA requires readable houses, paths and riverbank on 390px viewport.

Status: SPEC_ONLY; MAP19 not implemented. No main merge or runtime map replacement.
