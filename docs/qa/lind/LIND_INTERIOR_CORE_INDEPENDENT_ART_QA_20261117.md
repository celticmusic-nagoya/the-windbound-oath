# LIND interior core — independent art QA and method stop (2026-11-17)

## Actual evidence
- GitHub Actions [run 44012417592](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44012417592) SUCCESS, [artifact 14297665891](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44012417592/artifacts/14297665891).
- Render `interior_core_pbr.png` SHA256 `137c4843f51a45a8a38744688732ac37a357ce9dab9115426f8ad5818a053d6a`; `interior_core_reference.blend` SHA256 `d62bb2ae2dded80a30b29cd645a15cfed8e775de461de9c33398b76b8706d0d6`.
- Verified prior local patch input: 86,764 source faces; 3,734 source open edges; 0 >2-face nonmanifold edges.
- 12 face-adjacency rings eroded: 48,105 eligible faces across 36 disconnected components; largest component 12,241 faces / 6,397 vertices; 551 new open boundary edges; 0 >2-face nonmanifold edges. Original publisher UV loop values preserved.
- Retopology NOT_RUN; normal bake NOT_RUN; game integration NOT_RUN.

## Visual inspection
**FAIL for cliff-production suitability.** Render shows two visually distinct large lobes connected by a narrow upper span, creating a large central gap. Highly irregular sawtooth termination edges, thin unsupported tips and a floating-surface appearance remain. It does not resemble a continuous grounded natural cliff face or a credible standalone game-world cliff asset. Source rock microdetail is retained, but this is only a diagnostic reference.

## Root-cause interpretation
- Erosion by a fixed face-ring count removes source perimeter triangles but **does not** construct terrain-backed support, bridge scan holes, or ensure a geographically sensible patch footprint. The 36 resulting components demonstrate fragmented usable interiors.
- Choosing the largest connected component is a graph/topology criterion, **not an artistic or geological suitability criterion**. Do not mistake successful mesh QA for usable cliff shape.
- The 551 open edges are a new crop boundary, not an indication of a watertight production mesh.
- Do **not** try more erosion depths or different component-size thresholds as a cosmetic repeat. Stop this method as a final cliff candidate.

## Gates
G1 BLOCKED (canonical placement/scale absent); G2 FAIL (production art); G3 PASS (SHA, source UV, extraction, Blender reopening), FAIL (production shape/open edge treatment); G4 NOT_RUN.

## Next production architecture
Build **macro cliff support independently from approved geography and terrain design**, and use the original scanned surface as **local embedded rock detail** with explicit contact/transition zones. Artist- or rule-guided patch selection must check camera-visible silhouette, supported edges, scale, and composition before retopology/bake. Preserve source publisher scan and exact provenance. Do not perform another global Voxel Remesh or blind erosion rerun. No canonical or main edits.
