# Morwen female basemesh — measured envelope comparison (2026-11-17)

Status: TECHNICAL MEASUREMENT ONLY; no character G1/G2/G4 approval.

## Reproducible evidence
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43974285450
- Artifact ID: 14280637543
- Evidence path: `diagnostic_renders/diagnostic_manifest.json`
- Source: Blender Studio Human Base Meshes v1.4.1 (CC0), unmodified source.
- Measurements: world-coordinate vertex bounds of the full body mesh, as recorded by `render_basemesh_comparison.py`; dimensions in Blender units. NOT anatomical landmark measurements.

| Source object | X width | Y depth | Z height | Width/height | Depth/height |
|---|---:|---:|---:|---:|---:|
| GEO-body_female_stylized | 0.72088 | 0.27319 | 1.61691 | 0.4458 | 0.1690 |
| GEO-body_female_realistic | 0.84223 | 0.28259 | 1.63932 | 0.5138 | 0.1724 |

The realistic mesh is wider relative to its total height. This does not establish shoulder width, hip width, anatomical realism, head height, 7.75-head compliance, or artistic suitability. The source meshes have not been modified or adopted.

## Required next measurement gate
1. Use Blender geometry plus reviewer-confirmed head-top, chin, acromion, waist, hip, crotch, knee, ankle, sole landmarks to measure both meshes in the same coordinate frame.
2. Verify whether the asset's world transform or hidden parts affect measurements. Do not infer head landmarks from alpha image bounds or whole-mesh bounding boxes.
3. Produce comparable front/back/side render overlays at equal body height and neutral camera scale; record all landmarks and uncertainty.
4. Compare against the director's 7.5–8-head target and five canonical Morwen sources; any proposed anatomy changes remain a separate candidate.
5. G1 canonical model BLOCKED; G2 NOT_RUN; G3 diagnostic render PASS only; G4 NOT_RUN.

No approved source was changed, no main merge, no release.
