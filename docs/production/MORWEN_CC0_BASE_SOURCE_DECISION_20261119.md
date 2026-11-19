# MORWEN — zero-cost CC0 base-mesh sourcing decision (2026-11-19)

Status: **SOURCE IDENTIFIED / IMPORT NOT_RUN / SCULPT NOT_RUN**. Scope: PR #427, Issue #426. This is not a model acceptance or G2 pass.

## Verified source and licensing
- Official MakeHuman Community license: https://www.makehumancommunity.org/about/license.html
- Source license: https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md
- Blender-native MPFB2 license: https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md
- System/target asset packs: https://www.makehumancommunity.org/assets/assetpacks/index.html
- Core MakeHuman and MPFB2 **graphical base meshes, targets and bundled assets** are **CC0**; application/add-on code is GPL/AGPL, separately. The MakeHuman project does not claim ownership of exported models. **Third-party community asset packs can have other licenses**: inspect every exact asset before importing. Do not assume all MakeHuman community assets are CC0.
- **Avoid MB-Lab AGPL model/database** as an unreviewed base for a proprietary game: its generated meshes may carry AGPL obligations. Source: https://github-wiki-see.page/m/animate1978/MB-Lab/wiki/Asset-Licensing

## Proposed no-charge production experiment (not yet executed)
1. Pin MPFB2 version, source URL, exact bundled CC0 base mesh file, SHA256 and Blender 5.2.4 compatibility; do not install arbitrary GitHub code without reviewing dependencies.
2. Import an **unmodified** CC0 human base into a separate collection of the existing four-view reference .blend. Record source license and hashes. No paid API, credit usage, GPU rental or external account requirement.
3. Compare silhouette and landmarks against the four Layer 0 views before any artistic deformation. Record front/side/back differences; check orthographic alignment and image offset. This is a **technical candidate**, not the Morwen design.
4. Only after compatibility and reference fit, perform actual authored sculpt for facial planes, bob, eyes, glasses, clothing and equipment as distinct modules. A default MakeHuman model, automated morph slider changes, procedural hair tubes or UV spheres **cannot** be declared G2 PASS.
5. Independent art QA on renders and editable .blend; topology/UV/rig G3 later; game G4 separately.

## Gate
G1 **PARTIAL** (Layer 0 body/hair reference SHA confirmed, final accessories pending); CC0 source **license research PASS**, exact downloaded mesh SHA **NOT_RUN**; Blender import **NOT_RUN**; actual design sculpt **BLOCKED pending sculpt-capable production**; G2/G3/G4 **NOT_RUN**. Do not create a new PR or merge main.
