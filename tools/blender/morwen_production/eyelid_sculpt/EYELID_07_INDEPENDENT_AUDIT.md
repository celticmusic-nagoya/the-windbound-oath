# MORWEN EYELID-07 independent algorithm audit

Task: PR #321 topology/correspondence only. Base 5a2dd4a0e8e1650be887cb6c07b49a5668141c2e. No deformation, source save, model regeneration, main merge or adoption.

## Evidence and findings

Downloaded Actions run 43660784139 artifact 14139778100 (ZIP SHA256 ebbd31779e897c1bfaa393028c0074dbc959368bc64e4890dfc92a0faae91188), run commit 166278a20e7bc823f1443e0309d8ed6131022307. Captured input blend SHA256 bc230eeb617c1e74bddae5701ca22ca7b345974c716301fe3729106fb9d58f1d. Original three JSON files retained byte-for-byte under evidence_07. This run predates the audited code HEAD; its camera PASS is not a new splitter/closure PASS.

Both sides have exactly 28 unique vertices and 28 unique edges, one connected cycle, degree two everywhere, no open endpoints. The splitter now verifies the complete cycle edge set rather than trusting graph flags. Duplicate edges, missing edges/coordinates, branching, duplicate/coincident vertices, nonfinite/zero geometry and invalid sample counts fail closed. Anchor order was previously silently sorted by ring index: fixed to preserve the caller's direction.

Source authoring coordinates in EYELID_05_REPORT.build.lid_{R,L}.canthus_vertex_world identify inner/outer IDs uniquely within the six-decimal coordinate rounding bound sqrt(3)*0.5 micrometres (+1 nanometre). R: 1397 -> 1351; L: 1264 -> 1207. These match the independent maximum-distance pair proposal. Source authoring confirmation is not formal anatomical/art approval. For future sources, bind reviewed IDs and an orthonormal eye-local frame to the source hash and mesh fingerprint; reject nonunique matches or stale IDs, require overlay review at front, both 45 degrees and profile. Do not adopt nearest vertex without a bounded unique match. Current world-X/world-Z semantics are explicitly provisional, not a reusable calibrated frame.

CORRESPONDENCE_07.json contains 33 samples per side, both edge endpoint IDs and interpolation weights, ordered chains, source hashes and proposed upper/lower labels. Samples interpolate existing edges; they do not add vertices or imply 33 distinct mesh vertices. Both chains share exact endpoint IDs and direction. Labels A/B remain in the low-level API; candidate upper=A/lower=B for this capture.

No projected nonadjacent edge crossings or edge-length outliers under diagnostic [median/5, median*5] policy. Projection is the candidate canthus/superior plane; conservative projected crossings block proposals. This does not establish absence of surface intersections, collision with eyeballs, reversed faces or deformation failure. R lengths: 1.46435–8.14182 mm; L: 1.46435–8.14181 mm. Full edge range and median are in JSON. The diagnostic outlier factor is not an approved production stretch tolerance.

## Executed verification

- Python unittest discovery: 20 PASS (includes five inherited baseline cases repeated in regression class).
- Blender 4.3.2 headless: same 20 PASS, including replay of actual model vertex IDs, edges, XYZ and recorded source anchors.
- Actual .blend not present in workspace or supplied artifact. No fresh model load/render, complete mesh/56-key fingerprint comparison or occlusion test was executed. Blender 5.3.0 source camera checks are inherited artifact evidence only. Do not describe replay as a fresh Blender model QA.
- Scripts only read captured JSON and create a new output via exclusive creation. No bpy mutation or unvalidated deformation bypass.
- Existing failed deformation ledgers untouched; stopped transfer/pivot families not retried. This is a read-only correspondence method, not another closure generation attempt.

## Gates

| Gate | Result | Evidence / remaining work |
|---|---|---|
| G1 source/canon protection | PARTIAL / full canon BLOCKED | No assets or keys edited. Original capture reports 56-key preservation. Fresh full-key hashes not run; canonical binary comparison unavailable. |
| G2 independent art | NOT_RUN | Reviewed formal canthi/eye-local frame and expression/view render matrix still required. |
| G3 technical | Correspondence subtests PASS; full closure FAIL (inherited) | Original report eyes_hidden_when_closed=false, socket_show_through_zero=false, corner_no_flip_required_states=false. Fresh .blend collision/occlusion and 56-key regression NOT_RUN. |
| G4 game/Android | NOT_RUN | No integration or device test. |

## Reproduce

```sh
python -m unittest discover -s tools/blender/morwen_production/eyelid_sculpt -p test_split_lid_loop_07.py -v
python tools/blender/morwen_production/eyelid_sculpt/correspondence_audit_07.py tools/blender/morwen_production/eyelid_sculpt/evidence_07/EYELID_07_TOPOLOGY_MAP.json /tmp/new-correspondence.json --baseline tools/blender/morwen_production/eyelid_sculpt/evidence_07/EYELID_05_REPORT.json
```

Next deliverable: source-bound reviewed canthus calibration and unchanged saved blend with all 56 key fingerprints; then separate candidate closed-target authoring and geometry/render validation. This patch does not claim the visible eyeball defect is resolved.
