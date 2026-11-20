# Morwen legacy face-part isolation QA — 2026-11-19

**Real Blender 5.2.4 execution PASS**: [Actions run 44527941629](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44527941629), artifact [14532571931](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44527941629/artifacts/14532571931), ZIP digest `sha256:d763a9fd9c045d2f60ea35aa088cda6cdda263b591b2de180a878081c3dfc78d`.

Source PR #316 `MORWEN_ELM_04_CANDIDATE.blend` SHA256 `6c5a9919fd6733a0a1ec8d261fb647e5825cb3dfbc4092ed12c0e7baab26de5c` was verified before duplicate. Source 2,750 Face polygons. New `MORWEN_FACE_PARTS_316_ISOLATED_CANDIDATE.blend` SHA256 `30b42f291e8838002a65635ecd7e5a57b208ae051e5d5e916835169b933cff5a` (8,666,439 bytes).

| Region | Source faces | Isolated faces |
|---|---:|---:|
| FaceEyeline | 384 | 384 |
| FaceEyelash | 224 | 224 |
| FaceBrow | 160 | 160 |
| **Total** | **768** | **768** |

Reopen PASS in Blender 5.2.4; retained 58 shape key blocks, 1 UV layer, 83 vertex groups, 1 modifier. Original file untouched. Candidate isolation is a **structural milestone**, not G2 artistic acceptance or G3 deformation PASS. Shape-key and weight counts preserved, but individual evaluated deformation, material alpha and game integration NOT_RUN. Older PR #318 eyelid G3 FAIL remains.

Next: compare neutral/Blink/Joy evaluated geometry against original PR #316; render actual front/three-quarter/closed-eye source vs isolated module with correctly loaded textures and neutral lighting. Then independent G2 against Morwen canonical Layer 0 four views. No paid API, new PR, merge or official adoption.
