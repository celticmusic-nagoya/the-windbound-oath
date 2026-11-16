# WORLD / ROUTE: evidence and production profiles

The existing PR #350 runner/workflow is extended, not replaced. `evidence` retains its read-only D partition. `production` builds actual independent bounded WORLD/ROUTE geometry from the two authored Blender recipes, reopens saved blends in a separate process, renders three views, verifies hashes and measured technical subsets, and retains all artifacts. No AI API, main merge, adoption, publication or deletion is automated.

## Current execution

Branch `feature/lind-geology-route-production-01`, Draft PR #351. WORLD and ROUTE ran as two independent producer workers; root reviewed saved blends and actual images. The bounded candidates are **not final-quality deliveries**: two WORLD art families and the ROUTE automatic-facing family reached their same-defect two-failure stop. G2 remains FAIL. See `docs/qa/lind/geology-route-production-01/report.md`, exact-image review JSON and the cumulative ledger. Earlier #346 failures are preserved byte-for-byte and linked by SHA; no historical counts are reset.

Formal original PNG SHA: `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.
Immutable D blend SHA: `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`.
The original, approved event CGs, main AGENTS, HANDOFF and scene interface were checked. `Blender.md` was not found in the workspace or GitHub main root (404); this missing document is recorded, not claimed read. Private main reference headers/status were checked without copying private lore. Physical coordinates, scale and scene placement remain unapproved.

## Ownership and dependencies

- WORLD: `production_world.py`, `world/attempt-*`. Final selection: `world/attempt-04-technical/`. The large shared clipped envelope was stopped; independent inclined outcrops and actual bedrock-triangle soil volumes are separate candidates. Last technical repair changes one folded talus skin only; all other 463 mesh vertex/face hashes remain unchanged.
- ROUTE: `production_route.py`, `route/`. D terrain/bridge is the fixed SHA WORLD interface. Actual road-bearing bodies, abutments, shoulders and a shared junction were produced. Existing supports remain frozen through the stone-facing changes. A named fully buried invalid decoration cell was excluded after dense occlusion measurements; a visible invalid cell hard-fails the generator.
- `production_interface.json`: candidate Z-up frame, immutable D surface objects, no adopted metric transform, no scene-assembly authorization. The new WORLD cliff is a local sector, not silently inserted into D; ROUTE must not consume it until an approved common interface exists.
- HOME/ECO remain disabled. No one edits the same blend concurrently. Do not append both contextual scenes wholesale.

The same workflow runs WORLD/ROUTE in parallel, then `evidence-integration` **only when both tested technical subsets pass**. Integration verifies artifact hashes and packages references; it is not scene assembly, full G3, art acceptance or game integration. G1 remains full-review BLOCKED and G4 NOT_RUN. G2 cannot be set to PASS by deterministic config. CI inherits the known family FAIL and does not pretend to evaluate its own new images.

## Run / resume

```sh
python3 -m unittest discover -s tests -p test_map_pipeline.py -v
python3 tools/map_pipeline/pipeline.py key --profile production --unit WORLD --runtime 4.3.2
python3 tools/map_pipeline/pipeline.py run --profile production --unit WORLD --runtime 4.3.2 --base /tmp/lind-production-evidence
python3 tools/map_pipeline/pipeline.py run --profile production --unit ROUTE --runtime 4.3.2 --base /tmp/lind-production-evidence
python3 tools/map_pipeline/pipeline.py integrate --profile production --runtime 4.3.2 --base /tmp/lind-production-evidence
```

The two `run` commands may run concurrently. These commands reproduce **already authored, failed art candidates for technical evidence**, not new artistic correction trials. Never use CI or a renamed output directory to resume a stopped modelling method. Before a new creative trial, consult both the original and new cumulative ledgers, document a genuinely different causal method and measurable acceptance checks, and remain within approved non-destructive scope.

Pushes touching the pipeline/tests on this production branch select the production profile; the existing #350 branch selects evidence. Only push is subscribed, avoiding duplicate PR/push builds. Workflow dispatch is usable once the workflow is available on default; no automatic workflow dispatch or rerun loop exists. While Codex is stopped, an already-triggered deterministic graph continues to its gates. It cannot author new shapes, repair art, restart Codex or approve placement.

Input keys cover protected bytes, runtime, unit-specific producer, independent QA/runner code, settings, fixed interface and original history. WORLD code-only changes do not invalidate ROUTE (tested). Shared runtime/QA changes intentionally invalidate shared evidence. Successful exact caches verify blend/PNG/JSON output hashes and skip Blender; failed exact caches refuse another Blender execution. No prefix fallback. GitHub cache eviction and 14-day artifact expiration remain limits; download evidence before expiry and never manually repeat a known unchanged failure after eviction. No permanent cross-branch failure database is claimed.

Each unit artifact contains its blend, `overview.png`, detail (`detail.png` or `junction-detail.png`), `gameplay-distance.png`, `settings.json`, `interface.json`, producer manifest, independent `qa.json`, state and logs. `gameplay-distance` is a Blender composition at a study display distance, **not a tested game camera or actual runtime image**. Run summary and handoff artifact name exact unit artifacts and image paths. Use authenticated `https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/<RUN>/artifacts/<ID>` links; preview/download requires repository access. GitHub connector ZIP download works when a shell redirect host is blocked. Never claim a CI image visually checked merely because an artifact exists.

## QA limits and token use

Independent QA uses evaluated saved geometry, closed/manifold/winding/area checks, packed original SHA, actual manifest hashes, road triangle vertices/edge midpoints/centroids/interiors, support/burial/grade, coplanar-road overlap and shared-junction contacts. WORLD soil root tests preserve raw vertical-ray misses; a boundary miss is corroborated only by an exact .025Z-offset correspondence to the named actual bedrock triangles within .0001 candidate units. This addresses numerical triangle-edge misses, not real unsupported interiors. Both before/after diagnostics are retained.

Global unintended intersections, geotechnical/structural loading, collision/navmesh, runtime movement, performance and actual Android are NOT_RUN. Image reviewers separately evaluate silhouette, naturalness, material/detail, CG fit and display distance; technical PASS never promotes these gates.

Hand off only task IDs, changed paths/diff, necessary settings, input/output SHA, QA summary, diagnosed cause plus last 35 relevant log lines, image hashes and image/artifact references. Full logs and all mesh rows remain evidence artifacts and should be read only for a specific diagnosis. Preserve approved geometry SHA rather than regenerate it. No numerical token-saving claim is made without measurements.

## Next boundary

Do not expand these failed art families to the whole village. Next safe autonomous work is to validate a structurally different reference-driven sculpt/load-bearing masonry recipe and shared boundary contract, then execute one bounded trial with independent image QA. No credible new art method is represented as implemented here. Metric/camera/placement adoption still requires the missing design decision; G1/G2/G3/G4 and director adoption gates remain intact.
