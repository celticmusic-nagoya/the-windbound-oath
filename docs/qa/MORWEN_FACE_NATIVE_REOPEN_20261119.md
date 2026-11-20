# MORWEN face module native Blender 5.2.4 reopen — verified 2026-11-19

Workflow [run 44516535951](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44516535951) **SUCCESS**, artifact **14526017472** `morwen-legacy-face-reopen-qa` (expires 2026-12-03), artifact digest `sha256:187b1614d39fb4843f02675eaa275651b968bf06c968df38e15853a98428e97e`. Original source .blend SHA-256 values are recorded in `docs/qa/MORWEN_LEGACY_FACE_MODULE_RECOVERY_20261119.md`.

| Source | Mesh object | Vertices | Faces | Shape keys | UV | Armature |
|---|---|---:|---:|---:|---:|---|
| #316 ELM04 | Body | 7,797 | 11,646 | 0 | 1 | yes |
| #316 ELM04 | Face | 1,822 | 2,750 | 58 | 1 | yes |
| #316 ELM04 | MORWEN_Eyes | 1,122 | 1,120 | 0 | 1 | yes |
| #316 ELM04 | Icosphere | 42 | 80 | 0 | 1 | no |
| #318 EYELID05 | Body | 7,797 | 11,646 | 0 | 1 | yes |
| #318 EYELID05 | Face | 1,972 | 2,772 | 58 | 1 | yes |
| #318 EYELID05 | MORWEN_Eyes | 1,122 | 1,120 | 0 | 1 | yes |
| #318 EYELID05 | Icosphere | 42 | 80 | 0 | 1 | no |

Both files reopened successfully in **Blender 5.2.4 LTS**; `Armature` object present, Body/Face 83 vertex groups each, `MORWEN_Eyes` 2 groups. The eye mesh and Body counts are unchanged across the two candidates; Face changed +150 vertices/+22 faces in #318. **58 face shape-key blocks** means 58 key blocks, not necessarily 58 distinct expressions (includes Basis); earlier report said 56 expressions, inspect names before asserting.

**Important:** Lash/eyeliner cards are not separate mesh objects in the extracted scene structure (possible embedded mesh or material/alpha cards), so do not assert independent lash mesh is reusable without inspecting face mesh/materials/UV. The `Icosphere` is a 42-vertex unrigged object; do not mistake it for a production eye. The report establishes topology counts and file loadability only, **not** artistic correctness, shape-key motion, normal integrity, or license clearance.

**Gate:** native reopen PASS; G3 structural inventory PASS (limited scope); #318 historical deformation G3 FAIL remains; G2 independent visual QA NOT_RUN; final sculpt NOT_RUN; G4 NOT_RUN. Next: examine mesh material faces and lash topology, source provenance, neutral/blink renders and compare four-view reference before any reuse. No paid API, main merge, new PR or formal acceptance.
