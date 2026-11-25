# TWO Blueprint Engine v1 (Claude, shared infrastructure)

Owner: Claude (common Blueprint Engine, per `CROSS_AGENT_OWNERSHIP_AND_QUOTA_FALLBACK_20261123.md`).
Execution contract owner: Codex, PR #468 (`tools/production_qa/shared_blueprint_contract.py`,
`shared_factory_stage.py`). This package **imports** that contract; it defines no competing
target/observation schema and no Factory, Session Controller, checkpoint, CAS, lease, fencing or
Actions dispatch. Asset blueprints and native authoring stay with the asset owners (#427, #364, #421).

| Module | Function |
| --- | --- |
| `sources.py` | Source Adapter: SHA-256, bytes, role, projection, coordinate system, units, scale, provenance, license; PNG/.blend/.vroid/JSON metadata without extraction; expected-SHA mismatch fails closed |
| `evidence.py` | `NATIVE_MEASURED`, `OFFICIAL_SOURCE_MEASURED`, `RECONSTRUCTED`, `ESTIMATED`, `PROVISIONAL_DESIGN`, `UNDETERMINED` |
| `geometry.py` | Geometry Blueprint: landmarks, dimensions, sections, silhouettes, connections, material regions, mesh/UV/rig specs, anchors, bounds; target groups; open questions |
| `measure.py`, `measure_blender.py` | Measurement Engine and read-only #468 Factory adapters (`measure`/`reopen`/`finish`; `edit`/`correct*` raise) for official images and Blender 5.3.0 natives; per-metric uncertainty and SHA-bound evidence |
| `residual.py` | `|r|+u<=t` PASS, `|r|-u>t` OUTSIDE, else HOLD, using #468 `metric_state`; HOLD list for remeasurement |
| `contract.py` | Correction Contract: compile #468 targets; operation qualification registry; only qualified corrections are forwarded; dependency/protection/qualification mismatch -> `factory_ready=false` |
| `export.py` | Canonical JSON, `SHA256SUMS` + `ledger.json`, blueprint preview SVG (no source pixels), read-only Studio record (`adoption=UNDETERMINED`, `publication=NOT_APPROVED`) |

Guard rails: UNDETERMINED carries no value and cannot be a target; 2D sources cannot assert a 3D
measured/estimated value (only `RECONSTRUCTED` with a named method and >=2 views, or an explicit
`PROVISIONAL_DESIGN`); occluded geometry cannot be "measured"; no canon change, adoption or edit.

## Run
```
cd tools
python3 -m unittest discover -s blueprint_engine/tests -t .     # bpy 5.3.0 enables Blender tests
python3 -m blueprint_engine.cases.lind_home --design measurements.json --native home_portal_checkpoint.blend --out OUT
python3 -m blueprint_engine.cases.morwen_layer0 --layer0 DIR --silhouette DIR/reference_silhouette_landmarks.json \
        --precision morwen_authored_sculpt/precision_blueprint_v2.json --vroid model.vroid --out OUT
```
`.github/workflows/two-blueprint-engine-qa.yml` repeats both cases on a clean runner (SHA-enforced inputs from
artifacts 14602858760, 14741418957, 14754066570 and the LIND-HOME evidence ZIP) and publishes
`deterministic.sha256` for cross-run comparison. Native and official-image bytes are not uploaded.

## Engine acceptance (v1.0 contract freeze)
* Contract: target/request/observation envelope, `metric_state`, and the one-sided `lower_bound`
  (`constrained_state`/`deficit`/`lower_bound_issues`) are the #468 implementations (applied in
  #468 `2747ac90`; `proposals/468-lower-bound.patch` is kept as the record of that change).
  `bounds.REFERENCE` is a parity oracle only (`test_reference_matches_468_contract`).
* Two-sided: `|r|+u<=t` PASS, `|r|-u>t` OUTSIDE, else HOLD. Lower bound `r=x-L`: `r-u>=0` PASS,
  `r+u<0` OUTSIDE, else HOLD; tolerance must be 0, never auto-corrected, no upper end invented.
* Interference (Factory monitor, tested through the engine contract): a correction stops when a
  non-affected metric moves beyond noise, PASS leaves PASS, HOLD becomes OUTSIDE, or a lower bound
  is crossed; a HOLD on an affected metric blocks the correction (one remeasure, then stop).
* Malformed / non-finite values, tolerances, uncertainties and tampered lower bounds fail closed.
* Real native loop: `cases/native_correction_loop.py` restores the #468 cross-run checkpoint
  (artifact 14880921255, SHA-pinned), measures OUTSIDE, executes the #468 qualified fixture
  correction through `execute_factory_stage` under a job-local lease, re-measures PASS in a new
  process, stores/reads back the checkpoint, and proves the stop paths (non-affected metric,
  lower-bound crossing, stale fence). `fault_injection_blender.py` is test-only.
* Reuse: character (Morwen Layer0 / VRoid face) and map (LIND-HOME, porch, native loop) cases use
  the same `Blueprint -> compile_target -> handoff -> evaluate -> Factory` path; cases may not
  redefine judgement functions (`ReuseTests`). Asset-specific edit operations stay with asset owners.

## Readiness (revision-specific, see owning PR record)
Engine contract and measure/correct/remeasure loop: see the PR record for the run that verified the
exact HEAD. Asset targets (porch re-issue, Morwen face definitions) and asset G1–G4 are owned by the
asset PRs and are not engine acceptance criteria.
