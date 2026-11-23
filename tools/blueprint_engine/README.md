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

## Readiness (revision-specific, see owning PR record)
IMPLEMENTED + ISOLATED_PASS for read-only measurement stages. Edit/correction execution is the
owner adapter + #468 Factory. G1–G4 of any asset are not assessed by this engine.
