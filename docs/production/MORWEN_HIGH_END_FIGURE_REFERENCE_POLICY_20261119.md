# MORWEN high-end figure / avatar reference licensing decision — 2026-11-19

Scope: existing PR #427, Issue #426; user permits **zero-charge only**.

## Source hierarchy
1. Official Morwen Layer 0 four-view art is canonical for design; protect original SHA.
2. Recovered PR #316/#318 native VRoid-derived Blender candidates: compare eyes, lashes, nose, lid static form and expression topology; **no G2 adoption without visual QA**. PR #318 deformation remains G3 FAIL.
3. MPFB / MakeHuman **bundled core assets**: CC0 licensed alternate base. Exact asset provenance, version, SHA and suitability must be confirmed before import.
4. High-end stylized figure sculpts, VTuber/VRM character topology, artist wireframes and shading studies: **reference only by default**. Mesh transfer or texture copying only when the exact item license explicitly permits it. No imitation of identifiable proprietary character design.

## Verified primary-source licensing
- VRoid Studio official guidelines: https://vroid.com/studio/guidelines ; standard pixiv-provided meshes are **not CC0**. Generally allows commercial games and editing exported avatars absent special clauses. Third-party items and sample avatars need individual terms. Distinguish software use rules from exported-model use.
- Official FAQ for models created in stable VRoid: https://vroid.pixiv.help/hc/ja/articles/4405813333657-VRoid-Studio%E6%AD%A3%E5%BC%8F%E7%89%88%E3%81%A7%E4%BD%9C%E6%88%90%E3%81%97%E3%81%9F%E3%83%A2%E3%83%87%E3%83%AB%E3%81%AF%E5%95%86%E7%94%A8%E5%88%A9%E7%94%A8%E3%81%A7%E3%81%99%E3%81%8B
- MPFB core assets license: https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md ; bundled mesh, targets, textures, rig assets CC0. Source code is separately GPL.
- MakeHuman official licensing: https://static.makehumancommunity.org/about/license.html ; core graphics CC0, MakeHuman code AGPL. Third-party community assets require separate verification.

## Reuse and QA matrix
- Face: learn volumetric cheek/nose/philtrum/chin transitions from figure sculpts, but create Morwen-specific forms from canonical art.
- Eye/lids/lashes: prefer inspecting actual #316 mesh, eyelash cards/materials, face shape keys and PR #318 failed lid behavior; do not restart stopped annulus/quad-patch procedures.
- Hair: study layered sculpted bob silhouette, asymmetrical bangs and game-optimized cards/mesh; no generic Bezier tube clumps as finished art.
- Materials: reference sculpt highlights, toon/PBR response and alpha sorting; compare final Android-sized view.
- Deformation: separate static G2 art from blink, smile and rig G3; G4 requires actual game integration.

## Status
Licensing research **PASS** for general terms, exact VRoid beta base asset provenance **BLOCKED**, third-party model asset licenses **NOT_RUN**, independent G2/G3/G4 **NOT_RUN**. No new 3D model was obtained or created by this decision. No paid generation or main merge.
