# MORWEN-BLENDER-30 | Professional 3D references and third-party asset policy

Status: ADOPTED FOR CANDIDATE RESEARCH ONLY. No third-party assets imported into production.

## Reference sources (verify per-item license and download terms before use)

| Source | Role | License guidance | URL |
| --- | --- | --- | --- |
| Blender Studio Rain v3 | Professional humanoid rig topology, joint deformation, facial controls | CC-BY; preserve author attribution, review scripts before opening | https://studio.blender.org/characters/rain/v3/ |
| Poly Haven | CC0 PBR materials, HDRI lighting, environmental props | CC0 per official license; do not assume preview/site branding is CC0 | https://polyhaven.com/license |
| Kenney | Modular low-poly environments and props for prototype comparisons | CC0 for game assets; verify individual asset page and bundled license | https://kenney.nl/support |

Do not extract assets from commercial games, copy proprietary character designs, or infer permissions from a free download button. For third-party assets, retain URL, author, license, version, retrieval date, original file SHA-256 and attribution in a separate manifest before import.

## Modeling workflow
1. Canonical lock: preserve four official Morwen views, asymmetric details, anchors, palette, and source hashes. Do not overwrite.
2. Reference anatomy: compare front/side/back shoulder girdle, clavicle, ribcage, waist, pelvis, neck; use high-quality open rigs for topology **study**, not silhouette copying.
3. Form: sculpt or construct continuous anatomy with independent front/back depth; establish primary, secondary and tertiary shapes.
4. Retopology: quad edge loops around shoulders, elbows, hips and neck; avoid cylinders and uniform rings as final anatomy.
5. Costume: independent layered garment meshes and knee-high socks; respect official design and remove unapproved accessories.
6. Rig and deformation: inspect skinning at shoulders, elbows, hips; test neutral, walk, turn, bend.
7. Lookdev: CC0 PBR materials/HDRI as reference, then adapt stylized palette to match official 2D assets.
8. Render five orthographic views + 3/4 with fixed camera and lighting, inspect actual images; CI PASS is not art PASS.
9. Browser/Android: export glTF/GLB, inspect geometry/materials, measure draw calls and size before engine integration.

## Quality gates
- Licensing: source manifest complete, no unapproved third-party assets committed.
- Geometry: manifold where appropriate, no intersections or disconnected anatomical pieces.
- Silhouette: human anatomy and canonical reference correspondence independently reviewed.
- Deformation: rig poses tested without clipping or extreme collapse.
- Render: five views visibly framed; alpha and background validated.
- Delivery: candidate-only Draft PR; no production overwrite, main merge or website publication.

## Next action
Repair camera framing (BLENDER-29) and inspect five actual PNGs before modifying the torso. Then prototype a **new** anatomical sculpt/retopology candidate informed by Rain rig construction and licensed references. Preserve old candidate for side-by-side QA.
