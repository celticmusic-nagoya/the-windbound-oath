# LIND-SPATIAL-CODEX-01 — independent QA

Reviewer `/root/qa`; separate from scene authors. **Final-quality adoption FAIL**. Technical source-review and render subsets pass after the packed-source repair; terrain remains a study candidate.

## Executed evidence

- Read current task policies and adopted map priority; directly inspected adopted world PNG and official sunset, stargazing and raid backgrounds. Paths and independently measured hashes: `source-research.json`. Historic checkpoint forbids reusing G2-failed grass/stone as accepted assets; no cumulative grass/stone production ledger was present in this branch, so historical failure counts were not reset or invented.
- Reopened source-review blend in Blender 4.3.2. Initial save had no image datablock/packed source; reported to author. After fake-user retention repair, independently reopened again: exact approved packed PNG SHA/3,586,379 bytes/1536×1024, 11 hidden UNPLACED semantic nodes, 7 LIND modular collections, zero geometry. Initial FAIL evidence retained.
- Reopened WORLD primary `world-renderable.blend`: exact packed source confirmed. The historical `world.blend` lacks packed image and remains failure evidence, not primary. File hashes for both blend files and all three 1152×864 RGBA views match producer manifest.
- Independently inspected geometry: continuous terrain 58,081 vertices/57,600 faces; 27 mesh objects; finite coordinates, no zero-area faces; bridge shell closed/manifold. Terrain and water intentionally have open surface boundaries; not automatically a defect. No UV layers, collision, LOD or resource acceptance established.
- Independently rendered overview from saved primary blend with 34% resolution/four samples, exit 0, decoded 391×293 RGBA PNG. This confirms reproducible execution, not full-resolution deterministic image equality.
- Existing topology tests: 8 PASS. Symbolic graph tests do not validate physical walkability.

## Measured blocking defects

| Route | Maximum geometric slope | End Z | Failure |
| --- | --- | --- | --- |
| Coastal promontory | 81.6° | -1.088 | Ends below ocean plane Z=0, descends cliff |
| Harbor | 77.6° | -0.506 | Ends below ocean, near-vertical approach |
| East bridge | 78.1° | 1.090 | Approach drops toward channel; bridge deck Z=5.8–6.1 remains disconnected |
| North farmland | 20.9° | 5.903 | Candidate only; runtime traversal not tested |

These measured failures substantiate the visual finding that surface-conforming ribbons inherit cliffs instead of creating walkable approaches. Paths/coordinates are unapproved candidates, so none of these dimensions becomes canon.

## Artistic and geographic review

Overview, coast and river views were actually opened and inspected. Final G2 is **FAIL**: smooth regular rock bands resemble a procedural layer pattern, grass/rock boundary creates visible sawtooth edges, study edges are abrupt cut planes, harbor access is a ribbon down a cliff, and bridge has no convincing abutments/road connection. Source references show fractured weathered cliff faces, continuous grassy tops and inhabited/material-rich scenes. No final ecology, buildings, wave/foam/shore transitions or estuary is produced. The two cliff concepts are topologically separate but exact source/CG view axes and meaningful geographic placement remain unapproved.

Corrective method hypothesis: author a road-specific grade-constrained profile with terrain cut/fill and explicit bridge abutments before surface decoration. For geology, use authored cliff fracture/slope/material segmentation instead of tuning the same periodic band shader. Preserve this failed candidate and attempt history. Review did not generate a second terrain candidate or reset producer retry counters.

## Gates

- G1 packed-source integrity subset: PASS for fixed primary files. Full spatial/event/canon concordance: BLOCKED.
- G2 final art: FAIL.
- G3 independent render subset: PASS. Physical routes: FAIL. Full mesh/material/collision/budget QA incomplete.
- G4 gameplay, SAVE adapter, navigation and physical Android: NOT_RUN.

No formal source replacement, main merge, publication, branch switch or production-code change performed by reviewer. See `summary.json`, inspection scripts/raw logs, geometry and route measurements for reviewable evidence.

## Candidate C — independent reassessment

C changes method to grade-constrained road centerlines plus terrain cut/fill and bridge crown profile. This is a structural change from surface-following ribbons. Independently reopened C `world.blend`: packed source SHA remains correct. All C blend/PNG file hashes match manifest; all three PNGs decode. C overview was directly inspected. Initial A failures above are retained; no prior candidate or failed evidence was overwritten by reviewer.

Actual mesh measurements confirm substantial grade improvements: coastal route 9.01°, harbor 18.21°, bridge 12.33°, all within producer's proposed 25° threshold. Harbor end is now Z=1.7, coastal end Z=7.591; former submerged endpoints are repaired. This threshold is a candidate design constraint, not canon or runtime navigation approval.

**C route continuity still FAILS.** Independent BVH vertical rays sample every left edge, centerline and right edge station against actual terrain and bridge triangles:

| Route | Buried center stations | Maximum burial | Consequence |
| --- | --- | --- | --- |
| Harbor | 9/141 | 0.1555 candidate units | Road disappears under terrain near shared junction |
| Bridge | 14/141 | 0.0378 candidate units | Claimed +0.05 deck clearance is not achieved |
| North farmland | 0/96 centers; 1 edge sample | 0.0193 candidate units | Local road-edge intersection |
| Coastal promontory | 0/141 | None | Grade/visibility subset passes; runtime still untested |

Measurements use a 0.015 candidate-unit burial reporting threshold, retain raw worst samples and station ranges, and do not infer meters. C's harbor issue is consistent with independently applied route earthworks overlapping and overwriting a shared junction. Bridge top is generated as a function of circular arch parameter, whereas road crown uses sine of linear X; the distinct profiles intersect despite the nominal offset. A maximum-grade assertion cannot detect either failure. See `candidate-c-route-occlusion.json` and rerunnable `inspect_route_occlusion.py`.

C overview visibly improves grade and waterway breadth, but keeps stylized smooth geology, sawtooth material boundary, incomplete shore/habitat/architecture and abrupt study edges. G2 final art remains FAIL. G3 grade subset PASS; G3 physical route continuity FAIL; G4 NOT_RUN. Repair requires a combined junction grading surface and road heights derived from the actual bridge deck surface, with independent burial/support tests; merely raising the nominal clearance does not establish joined routes.

## Candidate D — sampled clearance reassessment

Independently reopened saved D `world.blend`, SHA-256 `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`. Packed original is intact at exact approved SHA/bytes/1536×1024. D blend and overview hashes match manifest. Overview PNG decoded as 1152×864 RGBA and directly inspected. A/B/C failures remain recorded above; D does not retroactively pass them.

Reran independent geometry scripts against D, rather than trusting producer metrics. All **1,557 sampled points** (423 each for coastal/harbor/bridge; 288 for north farmland) are above actual terrain/bridge triangle surfaces:

| Route | Samples | Buried points | Minimum clearance | Maximum gap | Maximum grade |
| --- | --- | --- | --- | --- | --- |
| Coastal | 423 | 0 | 0.079694 | 0.167918 | 9.0068° |
| Harbor | 423 | 0 | 0.039884 | 0.197145 | 24.5002° |
| Bridge | 423 | 0 | 0.049916 | **0.444855** | 24.5002° |
| North farmland | 288 | 0 | 0.036374 | 0.221349 | 18.3111° |

Values are unapproved candidate units, not meters. Independent BVH uses stored polygon lists; producer uses evaluated `FromObject`. The independent minimum clearance is positive but differs from the producer's nominal +0.05 floor; exact +0.05 is **not confirmed**. This does not change nonburial PASS. Small floating-point grade deviations above 24.5° remain below the proposed 25° threshold. Global maximum gap is ~0.4449 at the bridge, **not ~0.22**.

D therefore earns **G3 sampled center/edge nonburial PASS** and **G3 sampled grade PASS**, confined to vertices and center stations. Road support, intersections between routes, unsampled triangle interiors, collision, navmesh and traversability are **not verified**. Raising a ribbon above terrain can remove burial while leaving a floating road; the remaining gaps and overview shadows require a designed supporting surface/road thickness and junction verification before full G3 acceptance.

G2 final art remains **FAIL**: unfinished cliff geology/material boundaries, sparse terrain study, missing production buildings/ecology and engineered road/shore detail. G1 full spatial/event review remains BLOCKED. G4 gameplay/Android remains NOT_RUN. No production file was edited by reviewer.
