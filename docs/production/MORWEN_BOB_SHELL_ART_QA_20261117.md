# MORWEN BOB SHELL — independent visual QA (2026-11-17)

## Evidence
- Workflow run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44027858379
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44027858379/artifacts/14303927273
- Model: `morwen_bob_shell_candidate_UNAPPROVED.blend`
- Views: `morwen_bob_shell_{front,back,left,right}.png`
- Manifest: `hair_shell_manifest.json`
- Source SHA-256: `d06e4ac3235a7569211b2f06fd330da488b10bf5a01e4201b36c6e0de1bf0dc6`
- Output SHA-256: `a3f0d66f05f33edb08869fad19d26a0ca7be4f3ad766ff4004e5904050038cc8`

## QA outcome
| Gate | Result | Evidence |
|---|---|---|
| G1 canonical correspondence | BLOCKED | Canonical artwork not independently overlaid in this review |
| G2 visual quality | FAIL | Four rendered views inspected |
| G3 mesh construction and four PNG file validation | PASS (limited) | 1,024 shell vertices, 960 shell faces, 5 fringe pieces, four valid renders |
| G3 topology/deformation/rig | NOT_RUN | No topology or animation deformation test |
| G4 in-game/Android | NOT_RUN | No game integration |

## Observed visual failures
1. Front: top of the hair is visibly flattened, with a hard horizontal/rounded edge; fringe lacks natural swept segmentation.
2. Back: bob reads as a smooth, rigid cylinder with a straight lower edge; no natural locks or nape transition.
3. Left/right: box-like silhouette with broad planar side walls, sharp diagonal bottom transition and no visible layered tips.
4. Across all views: hair appears as a helmet rather than individual stylized locks.

## Decision
Do **not** mark this candidate approved or merge to main. Do **not** attempt another parameter-only modification to the same continuous-shell approach. Preserve this artifact and SHA evidence as a failed visual candidate.

## Next production method
Keep existing source basemesh and render pipeline. Reuse a thin cap only if it conforms to the scalp. Construct several **independently editable, overlapping curved volumetric locks** with deliberate roots, bends, variable cross-section, tapered tips and asymmetric fringe; use reference-aligned silhouette controls and inspect front/back/left/right before optimizing to cards. HairHarpy v2 remains an optional GUI sculpting tool, not a CI dependency, until GPU/display and import/export are actually verified.
