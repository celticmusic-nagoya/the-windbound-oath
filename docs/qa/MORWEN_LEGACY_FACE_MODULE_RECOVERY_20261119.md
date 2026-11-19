# MORWEN legacy eye/lash/lid/nose artifact recovery audit — 2026-11-19

## Recovered actual files (not just PR descriptions)

| Origin | Workflow run | Artifact ID | Extracted .blend | SHA-256 | Status |
|---|---:|---:|---|---|---|
| PR #316 `feature/morwen-eyes-lids-mouth-04` | 43575126139 | 14106227834 | `MORWEN_ELM_04_CANDIDATE.blend` | `6c5a9919fd6733a0a1ec8d261fb647e5825cb3dfbc4092ed12c0e7baab26de5c` | RECOVERED |
| PR #318 `feature/morwen-eyelid-retopo-05` | 43587116653 | 14111116241 | `MORWEN_EYELID_05_CANDIDATE.blend` | `db9576531f7da777bc8a67af791af4b39b4975bf8d82adb3082c46742a556ff9` | RECOVERED |

Artifact ZIP SHA-256 digests as reported by GitHub: #316 `3441d72185f9509b9f83a66b48aacfb44f9eb4fdf8306381f2c5d77838405d29`; #318 `4ae0f735cb85dcd50c91f25901df15d21f1436b6768e20a2d2764844dc3cc976`. Artifacts expire 2026-12-14. The two extracted .blend files were hashed locally; they have **not yet been reopened by Blender in this audit**.

## Existing QA JSON directly inspected

- **#316 `ELM_04_REPORT.json`**: new `MORWEN_Eyes` mesh 1,122 vertices / 1,120 faces; 480 stretched VRoid eye-plate faces removed; nose @0.5 SHA locked; cards 410 vertices, opaque samples 7,776; no buried opaque texels across tested states; closed eyes hidden, no socket show-through; weights 1.0, 56 shape keys preserved; existing report G3 PASS for *executed technical checks only*. G2 NOT_RUN. Eyelid and mouth annulus retopo method **STOPPED after two failures**; old topology retained.
- **#318 `EYELID_05_REPORT.json`**: static canthus quad-strip retopo achieves measured front opening within 1px; no winding conflicts, no UV flips, shape keys preserved, nose and body unchanged. **G3 FAIL**: eyelid corner flips, incomplete closure, show-through and local deformation artifacts. Prior procedural deformation families stopped; **do not retry**.
- Both are generated from a VRoid source whose report identifies source SHA `1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b`; independently confirm original VRM provenance and terms before inclusion in game deliverables.

## Part-level reuse verdict (provisional, not G2)
- #316 eye geometry: **CANDIDATE FOR IMPORT AND ART QA**; must assess iris/eyeball shape, spacing and true topology in Blender.
- #316 lash/eyeliner cards: **CANDIDATE FOR IMPORT AND ART QA**; ensure transparency ordering, occlusion and facial expressions.
- Nose @0.5: **SOURCE-INTEGRITY PASS ONLY**, visual art quality unverified.
- #316 old eyelids: **REFERENCE-ONLY**, visual mismatch with Layer 0 eye aperture.
- #318 static lid shape: **REFERENCE/MEASUREMENT ONLY** until artist-defined corrective shape keys or alternative rig tested. **Not a deformable production component.**
- Mouth: **REFERENCE ONLY**, existing deform artifacts.
- Original source VRoid license and any third-party assets: **BLOCKED until exact provenance and license audit**. Do not call it CC0.

## Next safe work
1. Run pinned Blender 5.2.4 reopen/inspect on both recovered .blend files: mesh object names, vertex/face counts, shape key names, eye/lash/nose region structure, UV and armature dependencies; export JSON and neutral/closed-eye front+3/4 previews.
2. Review original PR #316/#318 render sheets and compare against Layer 0 four views. Record independent G2 per module.
3. Only then import verified useful modules into a new *candidate* collection of the four-view reference scene; keep untouched original source bytes and hashes, no formal acceptance.

**Gate:** recovery PASS; report-only part screening PASS; native Blender reopen NOT_RUN; independent art G2 NOT_RUN; new sculpt NOT_RUN; game G4 NOT_RUN. No paid AI, no main merge, no destructive replacement.
