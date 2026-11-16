# MORWEN-3D-CHARACTER-STRUCTURE-01 — production component plan

**Status:** DESIGN PLAN / NOT A MODEL / NOT APPROVED ART. Source authority: `assets/canonical/morwen/2026-11-16/MANIFEST.json` (five byte-preserved images). Preserve `main:docs/design/MORWEN_V561_CANONICAL_20261108.md` as historical approved reference; different design-sheet SHA must not be treated as identical. Read current main AGENTS.md and private canon before lore edits.

## Production intent
- Director withdrew the 2.8-head field sprite style and approved a full-game 3D visual direction. Current Morwen 3D proportion target is **7.5–8 heads**, subject to canonical image conformance and visual approval.
- The frozen CC0 VRoid base (`CONTACT_CAGE_DISABLED_08.blend`, SHA `9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4`) is **technical only**, measured ~6.57 heads and lacks character-specific costume/hair/hat/accessories. **Do not polish or promote this as final Morwen**. Reuse only verified rig/topology components that survive proportion/design QA.
- The new reference sheet and four Layer0 images are immutable source inputs, not textured meshes. Four views: front, back, anatomical facing-right, anatomical facing-left. Never mirror asymmetric features. Garter is on anatomical **right leg**, visible from rear. No arbitrary inferred fabric colors, ornament geometry, hairstyle or body measurements.

## Independent geometry modules and completion criteria
| Module | Deliverable | Review / risk |
|---|---|---|
| HEAD | character-specific head/face/ears, correct eyes/eyelids/mouth topology | silhouette and 4-view face proportions; no annulus/zipper eyelid retry |
| HAIR | independently editable hair mass, locks, fringe, rear silhouette | 4-view canonical match; intersections and rig deformation |
| HEADWEAR | hat and any approved trim as separate pieces | exact reference geometry/placement; do not invent motifs |
| BODY | proportion-correct torso, shoulders, pelvis and skin | head-count target; clean topology, normals and deformation |
| ARMS/HANDS | shoulder, sleeves, wrist, fingers | pose range, skin weights, clipping |
| LOWER BODY | skirt/lower garment, legs, shoes, socks | anatomical right-leg garter; front/rear/side asymmetry |
| OUTFIT | academy attire, seams, trims, material slots | preserve original asymmetry; cloth deformation/rig |
| ACCESSORIES | only reference-confirmed straps, books, decorations, props | independent attachments and slots; do not assume obsolete sprite motifs |
| RIG | named skeleton, deformation controls, attachment sockets | idle/walk/turn tests, foot IK and ground anchor |
| MATERIALS | measured/visually matched PBR channels and texture provenance | source/license and color-management consistency |

## Workflow / hold points
1. Confirm actual director-approved five-source image identity, hashes and visual details. **G1 remains BLOCKED** on reference precedence; byte hashes alone are not artistic approval.
2. Derive **measured** orthographic landmarks (head crown, chin, shoulders, waist, knee, heel, asymmetric accessories) from original images. Document ambiguity and occlusion; no fabricated millimeter values.
3. Build independent high-quality meshes using the best mix of sculpt, manual retopology, modifiers and procedural reproducible operations. A generic primitive assemblage is not a production candidate.
4. Review each geometry family at final gameplay viewing scale **and** close-up, then rig/deform, UV/PBR and 4-view renders. Record Blender version, script/seed, input/output SHA and method-family attempt history.
5. Compare actual 3D four-view renders side by side with all four source views, with independent G2; evaluate alpha, geometry, skinning and reproducibility under G3; runtime/Android G4 remains NOT_RUN until integration.
6. Do not modify the map/world lane. Camera/scale/renderer exchange remains a cross-team contract, not a guess.

## Existing technical evidence / blockers
- `morwen_four_view_capture.py` can create technical 512×768 four-direction PNGs from a frozen candidate; **not proof of final Morwen quality**.
- `verify_morwen_four_views.py` checks evidence presence/hash/dimensions, not visual conformance. Current synthetic unit tests are not real Blender renders.
- Earlier eyelid polar annulus/zipper method family exhausted two attempts; switch to a structurally distinct corner-anchored quad topology if resuming eyelid work, preserving cumulative failure ledger.
- Pending: source precedence resolution (G1 BLOCKED), complete character-specific 3D mesh (NOT_RUN), independent art review (G2 NOT_RUN), final rig/animation (NOT_RUN), game/device QA (G4 NOT_RUN).

**Safety:** no canonical replacement, destructive cleanup, main merge or publication without explicit director approval.
