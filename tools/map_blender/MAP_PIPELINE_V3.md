# TWO Map Production Pipeline v3 — adopted development direction (2026-11-13)

Scope: Rilde village 3D authoring / 2.5D browser presentation. This document is a workflow decision, NOT a canon-map acceptance or engine migration.

## MAP20 independent QA
Source: GitHub Actions #43322629915 (PASS). Artifacts: map20_report.json, rilde_map20_field.png, rilde_map20_cliff.png.
- Synthetic sightline test: 9/9 PASS.
- Real cinematic camera occlusion: NOT_VERIFIED.
- Navigation: NOT_VERIFIED.
- Art QA: FAIL. The field camera shows a flat rectangular base, planar blue river, bare houses, a straight bridge and a blocky grey band on the ridge. The cliff camera shows the village directly behind a small rise, not a credible sea-facing cliff sunset view.
- Conclusion: the unified heightfield is a useful geometry foundation, but the current result is not a production-ready village map.

## Production methodology, borrowing general techniques rather than copying third-party game assets
1. **World topology first:** canonical named landmarks, routes, river crossing, separate sea cliff and riverbank escape cliff. Keep coordinates explicitly provisional until reviewed.
2. **Terrain mesh:** Blender Python with heightfields and terrain masks. Build coast, sea, river channel, cliff and foothills as one continuous geological composition; apply geometry thickness where the camera reveals boundaries.
3. **Data-driven assets:** JSON for landmarks, prefab placements, camera targets, collision masks, and render settings. Deterministic seed and explicit object IDs; do not hardcode geometry in multiple scripts.
4. **Modular buildings:** create reusable timber/plaster/roof/chimney/door/porch components; use Blender collections and linked instances. Maintain consistent scale and entrances facing walkable paths.
5. **Procedural dressing:** Blender Geometry Nodes for grass, stones, reeds, garden plots, fences; distribute by slope, height, distance to roads and water. Use world-space noise masks, not polygon-by-polygon checker patterns.
6. **Art direction:** limited painterly palette, controlled warm/cool lighting, ambient occlusion, contact shadows, coherent roof silhouettes, and orthographic 25–30 degree field camera. Check small-screen readability.
7. **Export:** glTF 2.0 as optional intermediary for 3D browser tests; baked sprites/atlas remain valid for 2.5D. Preserve source .blend, PNG renders, JSON manifests and SHA-256.
8. **Runtime evaluation:** prefer the existing browser engine. Compare static/baked sprites with Three.js or Babylon.js only in an isolated benchmark before adding a runtime dependency. Godot is optional for prototype comparison, NOT automatically a production engine.
9. **Automation:** Python + Blender CLI + GitHub Actions; optional NumPy for array terrain operations, Pillow for image QC, TypeScript for game-side manifest schemas and coordinate/collision checks. Add dependencies only after measuring their value and compatibility.
10. **QA gates:** geometry/collision/route graph; cliff event camera occlusion (not only synthetic rays); identical-camera A/B renders; 390px Android visual QA; frame-time and memory budget; SHA and canon regression.

## Development order
MAP21-A: produce a versioned JSON map topology and 2D top-down schematic with route connectivity tests.
MAP21-B: rebuild terrain from that schema, add camera framing and river/coast masks; render two cameras.
MAP21-C: art-direction pass only after structural QA passes.
Do not patch the MAP18/19 ridge again; the two-try structural stop remains active.

No main merge, publication, or canonical runtime-map replacement without explicit approval.
