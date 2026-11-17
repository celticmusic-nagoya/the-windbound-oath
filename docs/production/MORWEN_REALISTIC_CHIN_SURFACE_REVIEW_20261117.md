# MORWEN — realistic basemesh chin cross-view surface audit (2026-11-17)

Status: **PASS geometric sampling; BLOCKED anatomical chin identification**. Diagnostic only; no production approval.

## Verified evidence
- GitHub Actions: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44034427990 (SUCCESS)
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44034427990/artifacts/14307505007
- JSON: `morwen_chin_probe.json`
- Source: official Blender Studio Human Base Meshes v1.4.1, `GEO-body_female_realistic`
- Source .blend SHA-256: `e5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a`; unchanged.
- Orthographic projection: 512x768 px, scale 2.05. Actual triangle surface intersections (BVHTree), 3 views, rows y=132,136,140,144,148,152,156,160; 31 horizontal samples per row at x=196..316 every 4 px.

## Verified hit counts (not landmark classifications)

| Image row | World Z | Front | Left | Right |
|---:|---:|---:|---:|---:|
|132|1.492996|15|17|17|
|136|1.482319|15|16|17|
|140|1.471642|12|16|16|
|144|1.460964|11|15|16|
|148|1.450287|11|15|15|
|152|1.439610|10|14|15|
|156|1.428933|10|15|14|
|160|1.418256|10|11|11|

All rows have surface intersections; **no scanline is verified as the chin or skull/neck transition**. Visible change in cross-section is not sufficient to classify anatomy. The current sparse horizontal sampling cannot distinguish chin, neck, jaw or rear skull.

## Gate
- Original-source integrity: PASS
- Three-view surface-raycast execution: PASS
- Reviewer-confirmed chin/head-top/sole landmarks: BLOCKED
- Actual heads-tall ratio: BLOCKED
- G1 full canonical match: BLOCKED; G2 artistic review: NOT_RUN; G3 diagnostic geometry: PASS only; G4: NOT_RUN

## Next decision
Do not start proportional mesh deformation on the basis of these scanlines. A qualified review of actual front and side surface with marked skull/chin/neck boundary is required, with 3D coordinates and supporting views. If independent landmark identification remains unavailable, prioritize other non-destructive, independently verifiable tasks instead of repeating the same scanline search.
