# AIDAN-PBR-INTAKE-DECISION-02

Status: PARTIAL SOURCE VERIFICATION / NO PRODUCTION APPROVAL

Evidence: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43454613943
Commit verified: 6399b05cbaad75ea7092286772dd39032ca9d1e7

## Exact provider API findings
- Poly Haven medieval_blocks_05: FOUND_TEXTURE
- Poly Haven medieval_wood: FOUND_TEXTURE
- Poly Haven dark_wooden_planks: FOUND_TEXTURE
- Poly Haven reed_roof_03: FOUND_TEXTURE
- Poly Haven thatch_roof_angled: FOUND_TEXTURE
- ambientCG Ground111: UNVERIFIED (after correcting the API request format)

## Stop condition / method switch
Ground111 has had two unsuccessful source checks using different endpoint formats (HTTP_404 and UNVERIFIED). Stop retrying the same asset without new evidence. Ground remains BLOCKED; select a new grounded, verified candidate in a separate intake, or defer ground PBR until later.

## Next approved-safe work
1. For five FOUND_TEXTURE entries, fetch provider files metadata, exact map URLs, resolution, file sizes and license evidence. Record provenance and SHA-256 for any downloads.
2. Keep material integration in an isolated candidate branch/artifact; do not overwrite approved files.
3. Produce five-view Blender render and compare against the approved Aidan home reference at final display size. Distinguish roof geometry from thatch surface texture.
4. G1 source existence is partial only; G2 visual FAIL; G3 candidate-render previously PASS but PBR not tested; G4 NOT_RUN.
5. No main merge, publishing, or canon promotion without explicit approval.
