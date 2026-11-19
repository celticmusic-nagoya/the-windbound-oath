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

## 2026-11-19 actual Blender evidence — unsuitable as neutral sculpt base
- Workflow run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44550645526 (SUCCESS, Blender 5.2.4)
- Artifact ID: 14543691271; source OBJ SHA256: 8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c
- Editable source import .blend SHA256: 7219eef7c284a166a686758ddb9149d87996d2dfcba9dae33d249ae0123b693f
- Geometry: 19,158 vertices, 18,486 faces, 154 disconnected components, largest 13,380 vertices; 1 material slot.
- Four actual orthographic render PNGs show a long-haired figure wearing a long dress/skirt and shoes, with an isolated square below the feet. This is **not** a neutral nude human sculpt base. The OBJ name `base.obj` was misleading; visual and geometry evidence supersede the prior source suitability assumption.
- Decision: **REJECT as Morwen production sculpt base (G2 FAIL source suitability)**; retain as provenance-marked technical import only. Do not reuse its geometry for Morwen or continue adjusting this source. Import/save/reopen/render pipeline G3 PARTIAL PASS; Morwen-specific G1 BLOCKED, G2 NOT_RUN on any authored replacement, G4 NOT_RUN.
- Next: locate and validate a truly neutral, separately licensed CC0 body source **before** any further Blender import, or use actual independent sculpt tooling. No new PR, no formal adoption, no main merge.
