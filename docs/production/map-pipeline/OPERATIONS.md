# WORLD / ROUTE deterministic evidence pipeline

Implementation baseline: PR #346 head `d94b43361f360cbdc448b0a3ffdb15d9dd23e02f`.
Branch: `feature/map-deterministic-pipeline-world-route-01`. This is a new orchestration method, **not new geology or new AI sculpting**. No approved assets, candidate D, historical scripts/logs or production maps are modified. PR base is #346's branch to keep the automation diff separate; never merge this PR automatically.

## Prior evidence inspected

- Existing `lind-source-review.yml`: source PNG SHA, pinned Blender 4.0.2 package SHA, source-review only. Existing run 43848206576 was confirmed success at b60ae5c. Reuse its exact Blender package verification; do not run the source-review generator again here.
- Formal visual source `assets/sources/lind-world-20261116/original.png`: SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. Packed original must match too. No lore, approved dimensions or scale are inferred. Formal full spatial review remains BLOCKED.
- D blend SHA `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`.
- `docs/qa/lind/spatial-codex-world/attempt-ledger.json`, PRODUCTION.md, independent/report.md: A/B geology family stopped after two G2 failures; C cut/fill failed actual BVH clearance; D has sampled clearance only. Original missing-file and denoiser failures retained. These are not reset by the new branch/pipeline.
- Existing `lind_spatial_assemble.py` requires approved placement/scale. It is deliberately not invoked: those approvals are missing. Evidence integration is not game/scene integration.

## Task graph and cache

`tools/map_pipeline/tasks.json` is the explicit task/approval registry. WORLD and ROUTE have no live build dependency and run concurrently from immutable D. WORLD removes route objects **in memory**, saves a new artifact and renders; ROUTE owns four road meshes and retains immutable terrain/bridge as QA/render context. Do not append both complete blends together. Their new output paths are CI artifacts, never original files.

Both PASS -> approved `evidence-integration` validates exact input/output hashes -> small handoff packet. A unit FAIL skips integration. HOME/ECO are registered but disabled until approved input adapters and meaningful QA exist. Their future dependency lists are proposals, not active jobs.

Input SHA covers unit ID, source/original bytes, runtime, scripts, settings, pinned package ledger and historical attempt ledger. Output SHA covers sorted hashes of blend, preview and QA. State records dependencies, method and gate results. Exact cache hits validate output hashes and do not install/run Blender or render again. No prefix fallback. Shared code/settings changes intentionally invalidate both units. Runtime 4.3.2 local and 4.0.2 CI have different keys; pixel/byte reproducibility across Blender versions is not claimed.

## Run and inspect

Push on the assigned feature branch or PR path changes starts CI; workflow_dispatch becomes available after the workflow exists on default branch. While it is unmerged, use a new in-scope commit to trigger the branch workflow. No schedule polling or AI service is required. Actions executes the entire approved deterministic graph while Codex is stopped. It cannot invent changes, restart Codex, evaluate art or repair failures.

Local verification (existing Blender 4.3.2):

```sh
python3 -m unittest discover -s tests -p test_map_pipeline.py -v
python3 tools/map_pipeline/pipeline.py run --unit WORLD --runtime 4.3.2 --base /tmp/wind-map-evidence
python3 tools/map_pipeline/pipeline.py run --unit ROUTE --runtime 4.3.2 --base /tmp/wind-map-evidence
python3 tools/map_pipeline/pipeline.py integrate --runtime 4.3.2 --base /tmp/wind-map-evidence
```

The two `run` commands can execute concurrently. Repeat them unchanged to see `REUSED` without Blender. Use a fresh output directory only after retaining failed evidence and diagnosing the cause; directory renaming is never a new method family.

Run summary links to the run and gives exact `map-WORLD-<inputSHA>` / `map-ROUTE-<inputSHA>` artifact names. Download `preview.png`, `qa.json`, `state.json`, `unit.blend`; the handoff artifact has `references.md` and `handoff.json`. Authenticated GitHub artifact links require repository access and expire after 14 days. Download images into the chat workspace and inspect them with image tools; there is no claim that a run link embeds an image in chat. Failed jobs still upload failure evidence; integration does not run. Upload/download GitHub service outages can prevent artifact preservation.

## Failure and resumption

No automatic rerun, retry loop or recursive workflow dispatch. The exact failed-input cache restores FAIL and exits without launching Blender. Interrupted attempts are blocked. Preserve `failure.json` (cause + last 35 relevant log lines), state, full log artifact and original historical ledger. Cache storage is opportunistic and may be evicted by GitHub; it is not a permanent cross-branch attempt database. Do not manually rerun an unchanged known failure after eviction. Download evidence before artifact expiry. Infrastructure failures need a causal environment fix; asset method counters remain cumulative in the historical ledger.

Codex resumes with only: task/unit IDs, git diff paths/snippets, input/output SHA, necessary changed settings, QA JSON, failure cause/tail, artifact/run references and images. Do not feed the repository, full blend or full logs into prompts. Look up full logs only if the tail cannot diagnose the cause. No AI job/API/token is invoked by CI. Cache hits and deterministic QA/rendering consume no AI tokens; no numeric token saving is claimed without measurements.

## Gates and next work

G3 PASS means only finite nonempty meshes, original packed bytes, a rendered PNG, and ROUTE sampled left/center/right BVH clearance plus a **provisional** <25 degree grade. It does not certify support construction, junctions, triangle interiors, collision/navigation, budgets or gameplay. G1 full spatial/event review remains BLOCKED, G2 remains inherited FAIL (even after these preview images are inspected), G4 NOT_RUN. No code path sets G2 PASS. Image-specific independent review and evidence binding would be required in a future change.

Not implemented: unattended AI modelling, automatic art judgement, new joint-constrained cliff/support geometry, independent production from approved new WORLD/ROUTE designs, geometry assembly, runtime/Android QA, durable cross-branch failure database, HOME/ECO adapters. Next: review CI images, approve a structurally different geology/support task with measurable acceptance checks, implement it separately while preserving D, then expand the validated runner to HOME/ECO. main merge, formal adoption, publication and destructive deletion are absent and remain human actions.
