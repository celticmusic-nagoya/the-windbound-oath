# LIND-SPATIAL-CODEX-01 execution index

Branch `feature/lind-spatial-codex-01`, Draft PR #346; baseline
`d18f7a5bdc7da997cace386f7b516c1a62c5366e`. Three independent sessions
performed TECH, WORLD and QA. Existing ChatGPT implementation was reused;
existing Claude masonry/vegetation packages were not edited. No old game
coordinates, final metric dimensions, game code changes or production adoption.

## Technical execution

The d18f path fix passes eight topology tests. The next CI failure was a missing
checksum file already implemented in #345; its exact bytes were introduced.
Saving an unreferenced image required `use_fake_user`; reopened packed-byte
verification was added. Python exceptions now fail Blender processes using
`--python-exit-code 1`. Original failed artifacts and logs are retained.

[CI 43848206576](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43848206576)
succeeded on code `b60ae5c9e781d6dd0622b1e2729b05d778e029b3`, pinned Blender 4.0.2.
`spatial-codex-ci.json` records log excerpts and Actions artifact ID/digest.
Local Blender 4.3.2 also generated and independently reopened the source-review
blend: exact adopted PNG, 11 unplaced semantic markers, seven LIND collections
(plus an empty default collection), no terrain meshes in the source-review file.
Technical evidence is under `spatial-codex-tech/`.

## Actual terrain production

Real terrain meshes and three actual render views per candidate are under
`assets/candidates/lind-spatial-codex-01/world/`. The production report,
settings, measured results and cumulative failure ledger are indexed by
`spatial-codex-world/PRODUCTION.md`. Independent visual, geometry, route and
source checks are in `spatial-codex-independent/report.md` and adjacent JSON.

This is a terrain-production study, not a finished village. A/B geological art
failed final-quality review; that method family is stopped. Route cut/fill is
a different defect/method and does not reset the geological-art failures.
Candidate dimensions, road limits, camera, bridge and harbor placement remain
unapproved. Source integrity and a successful render are not art acceptance.

## Gates and next work

G1 exact-source subset PASS; full G1 BLOCKED for approved metric/event concordance.
G2 final art FAIL. G3 source-review/render subsets PASS; full-world/route results
must be read from the final independent report, with failures retained. G4 NOT_RUN.
No real Android, navmesh/collision, game integration or final art approval.

Final delivered route study D is under `world/candidate-d/`: saved Blender 4.3.2
blend SHA-256 `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`,
plus an actual overview render, script and manifest. Independent QA measured
1,557 center/edge samples with zero burial and grades below the proposed 25°
study limit. This is G3 sampled nonburial/grade PASS only. The nominal 0.05
clearance floor is not independently confirmed; positive measured minima range
from 0.0364 to 0.0797. The maximum gap to support is 0.4449 candidate units,
so engineered support, junctions, unsampled interiors and traversability remain
unverified. G2 final art FAIL and full-world G3 nonacceptance remain unchanged.

Next geological method: explicit cross-section/joint-constrained rock sculpt and
erosion topology, with independently reviewed material/scan intake; do not rerun
the exhausted smooth-heightfield/striped-rock family. Estuary continuation,
harbor structural support, final bridge engineering and approved spatial/camera
contract remain necessary. No main merge, accepted-asset replacement, destructive
deletion or publication was performed.
