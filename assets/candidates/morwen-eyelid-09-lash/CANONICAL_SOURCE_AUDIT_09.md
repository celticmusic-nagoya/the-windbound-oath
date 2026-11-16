# MORWEN EYELID-09 — canonical reference audit (2026-11-16)

**Status: G1 BLOCKED.** This audit is read-only; it does not adopt, substitute, or change source imagery.

## Directly inspected repository references (default branch)
1. `docs/design/MORWEN_V561_CANONICAL_20261108.md` and `data/morwen-design-canonical.json`: director-approved design comparison sheet `7374.png` is actually JPEG/JFIF, 1536×1024, SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`. These documents explicitly say **binaryInGitHub=false**, that regenerated lookalikes and superseded v5.61 variants must not replace it, and production sprites are not approved.
2. `docs/design/MORWEN_OFFICIAL_3V_REGISTRATION_20261109.md`: director-approved right, left, back images; says binary upload **NOT YET COMPLETED** and points to director-provided `MORWEN_3V_DEPLOY_READY_20261109.zip` on Google Drive. Expected original PNG SHA-256: right `7eeff76ac07f631c14cb536e0e08346cfe815247a88520fb5a68cf0e877e5548`, left `d858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591`, back `9cf2f27448303aa60c603f0f32a7baada234fec8cae5108bf8103a9ae7547e69`. Intended target `assets/official/characters/morwen/turnaround/`. Note that approved **left** deliberately lacks satchel, hat flower/ribbon decoration and shoulder crest; preserve asymmetry, do not mirror or add these.
3. These are document claims and expected hashes, **not a direct verification of the source image bytes**. Before any image-guided UV projection or canonical bake, obtain exact binary, compare SHA-256, inspect visual source and resolve which front image is authoritative. The v5.61 comparison sheet is not a verified 4-view RGBA turnaround.

## Consequence
- Do not feed an unverified generated Morwen likeness to Claude as an approved source.
- Do not bake textures from screenshots or web images as if canonical.
- Geometry-only EYELID-09 collision investigation may proceed in an isolated candidate area, but no official image match PASS.
- G1 **BLOCKED**, G2 **NOT_RUN**, G3 current candidate **FAIL** (123 lash/cage triangle pairs), G4 **NOT_RUN**.
- Source files, original Shape Keys, model, branch base and published site remain unchanged.

## Next acquisition
Verify whether the original ZIP and 7374.png are available in the connected Google Drive or an uploaded file; only use originals with exact expected SHA-256. If unavailable, request the originals rather than inventing or replacing them.
