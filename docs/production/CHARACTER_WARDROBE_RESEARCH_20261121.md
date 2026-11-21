# Character wardrobe production research — 2026-11-21
Status: research shared by director approval; not tool adoption, asset acceptance or runtime verification. Owner Morwen #427 unchanged. Follow current AGENTS, blueprint-first and Morwen VRoid-first policies.

## Comparison
| Method | Role | Decision |
|---|---|---|
| VRoid layered clothing and custom textures | base silhouettes, layers, seams and motifs | first priority |
| OpenSew 2 | pattern-based sewing and draping | qualification candidate |
| Seamly2D | 2D pattern drafting | candidate |
| Blender Cloth | drape, large folds and corrections | downstream candidate |
| Garment Tool | pattern/sewing | license and compatibility check |
| Marvelous Designer | industry reference | paid; no purchase authorized |
| XWear | independent wearable packaging and fitting | interoperability candidate |

## Native-first modular workflow
W01: verify approved clothed references, hashes, directional asymmetry and visible material regions. Record attachment landmarks, silhouette, projection dimensions, tolerances and unknown depth; do not infer hidden anatomy or fixed real dimensions.
W02: obtain actual VRoid clothing UV templates and control mappings; record native template IDs and observed slider responses.
W03: layer native templates and refine shape, thickness allowances and overlap; preserve editable .vroid master and unique checkpoints.
W04: create original dedicated textures: cloth, seams, embroidery, trim, leather and metal distinctions. Approved crest only; no invented canon. Large folds in geometry, fine folds in normal maps where renderer supports them. Verify UV seams, texture scale, mip behavior and readability.
W05: qualify OpenSew 2 for unsupported garment structure on disposable body copy; inspect license, exact release/hash, Blender compatibility, reproducible sewing, exported topology/UV and deformation. No claim that advertised capabilities work locally.
W06: independently construct leather bag, straps, fasteners and accessories with thickness, attachments and asymmetry; preserve native-supported edits. XWear may be evaluated for independent exchange, not a substitute for native editing or final runtime integration.
W07: inspect actual four-view renders, clipping, skin weights, shoulder/elbow/hip movement, garment collision, reopen and independent art QA.
W08: separate authoring originals from game optimized export; measure WebGL/Android draw calls, texture memory, load and animation. Preserve existing gates G1–G4.

## Reference and caveats
- VRoid official help: https://vroid.pixiv.help/ — consult current layered clothing, texture editing and custom item import/export documentation. .vroidcustomitem is the native custom-item exchange route; verify template/category compatibility.
- XWear official help and packager documentation via https://vroid.com/en/studio and https://vroid.pixiv.help/ — external mesh packaging via Unity/VCC/XWear Packager is a separate workflow from native clothing editing. Auto-fitting is not proof of correct weights or collision. Validate version, license, actual import and game export; never assume arbitrary mesh becomes editable native garment.
- OpenSew 2: https://github.com/MarcelloMorettoni/opensew-2 — reported Blender 5.2 compatibility and pattern-based method; exact release, license, actual availability and supported feature list require upstream verification. Do not install or redistribute until qualified.
- Seamly2D: https://seamly.io/; Blender Cloth: https://docs.blender.org/manual/en/latest/physics/cloth/index.html; Marvelous Designer: https://www.marvelousdesigner.com/; Garment Tool remains a research candidate.
- Commercial games are quality references only, not sources for copying proprietary assets. Prefer original art and licensed materials.

## Gates / execution
Independent wardrobe blueprint/texture work may proceed in parallel without competing native model edits. One owner per conflicting file. Preserve official images and original files; no assets, external dependencies, paid tools, automation or canon changes authorized by this research merge. No premature transfer from VRoid. HairHarpy hair-specific priority unchanged.
Research summary only: installation, new garment mesh, native import/export, XWear interoperability, independent art QA and game QA NOT_RUN. Source links are research starting points; claims about specific versions and features require qualification before production reliance.
