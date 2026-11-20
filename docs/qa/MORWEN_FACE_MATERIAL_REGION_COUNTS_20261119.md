# MORWEN face material-region inventory — 2026-11-19

Verified [GitHub Actions run 44519896421](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44519896421) SUCCESS; artifact 14526309589 `morwen-legacy-face-reopen-qa`, digest `sha256:bb58e5050350adb478f39f0a7dd20784c84dc188b4ddcab33eb87936136bbfef`. Both native Blender 5.2.4 source scenes reopened and `structure.json` inspected.

| Material region | #316 faces / unique vertices | #318 faces / unique vertices |
|---|---:|---:|
| FaceEyelash | 224 / 150 | 224 / 150 |
| FaceEyeline | 384 / 260 | 384 / 260 |
| FaceBrow | 160 / 110 | 160 / 110 |
| FaceMouth | 496 / 386 | 496 / 386 |
| Face skin | 1,422 / 866 | 1,444 / 1,016 |
| EyeExtra | 64 / 50 | 64 / 50 |
| MORWEN_Eyes (separate mesh) | 1,120 / 1,122 | 1,120 / 1,122 |

Counts are unique **within each material region**, not disjoint vertex sets; shared boundary vertices may occur. The unchanged eye/lash/eyeline counts support *candidate recovery*, but **do not establish geometry byte identity, animation validity, art PASS, or independent separability**.

**Next technical QA:** extract region vertex/face topology fingerprints; compare #316/#318 vertex positions, face indices, UV and shape-key deformations, material textures/alpha and weights. Preserve source originals; perform isolated module export only after confirming boundary dependencies. Render neutral, blink and 3/4, then independent G2 review against canonical Layer 0 art.

G1 source references PARTIAL; structural inventory PASS; G2 NOT_RUN; #318 eyelid G3 FAIL remains; G4 NOT_RUN. No paid API, new PR or merge.
