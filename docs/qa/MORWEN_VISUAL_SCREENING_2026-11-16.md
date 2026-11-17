# MORWEN — independent visual screening of Blender QA output (2026-11-16)

## Provenance
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43849597580
- Artifact: `morwen-render-qa-loop` (artifact ID 14217077616)
- Render #2 SHA-256: `f2814cbc7ac081e991ed9b5c6912c1a6b8995b475089d015fa9871d3dfc66870`
- Source candidate SHA-256: `9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4`
- Canonical reference set: `assets/canonical/morwen/2026-11-16/MANIFEST.json` (five approved image sources, not modified)

## Observations and gates
- G1 design conformance: **BLOCKED**. Existing candidate has not been compared in four orientations against the five canonical references. Current output filename says `FRONT`, but visual screening suggests a **rear-facing** silhouette (back-of-head and back of garment visible). Orientation must be independently established using approved reference and model coordinate convention before front QA is accepted.
- G2 artistic quality: **FAIL (screening only)**. The visible candidate is an untextured gray T-pose with no detailed hairstyle, face, finished clothing, accessories or material fidelity. It is not a completed Morwen asset. This is a candidate-level finding, not a rejection of the canonical reference art.
- G3 framing subgate: **PASS** for image #2 only. 512×768 PNG; measured vertical occupancy 72.40%, unclipped; source hash unchanged. **Full G3: NOT_RUN**, because direction, four-view rendering, transparency and topology/performance are not yet validated.
- G4 game integration/Android: **NOT_RUN**.
- Overall formal adoption: **BLOCKED**.

## Production handoff (non-destructive)
1. Lock orientation convention (model forward axis, camera positions, anatomical right/left), based on verified source and canonical front/back reference. Do not silently relabel the rear view as front.
2. Produce and QA a complete **7.5–8 heads** proportion master from canonical references before adding detail. Existing frozen candidate is **not** the formal proportion master.
3. Create independent editable modules for face/head, hairstyle, torso/garment, sleeves/hands, skirt, socks, footwear, asymmetrical garter (anatomical right leg), and accessories **only where verified by references**.
4. Render four directions with canonical-image side-by-side comparisons and per-view hashes. Preserve source art unchanged; use a candidate branch and separate Art QA evidence.
5. Perform independent artistic QA, then technical geometry/alpha/rig QA, then game-size and Android QA before any adoption proposal.

## Loop protection
- Framing solver has succeeded; do not spend more cycles on camera zoom absent a new reproducible defect.
- Do not rerender unchanged frozen geometry as a substitute for actual modeling.
- No AI generative mesh editing or artistic QA is claimed to be running in GitHub Actions.
- No main merge, canonical replacement, release or publication is authorized.
