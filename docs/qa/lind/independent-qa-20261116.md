# LIND independent QA — 2026-11-16

Reviewer `/root/qa`; baseline `c0223b538c3a8b20329ea847c7237b424ccfac4a`. Separate from STORY and INTEGRATION authors. No production file modified. Evidence: `independent-qa-20261116/summary.json` and adjacent raw logs.

## Executed results
- 10/11 selected existing event/SAVE Node tests PASS. `save_compatibility.test.cjs` FAIL before assertions: `startup_race.test.cjs` expects a missing `$('#devGrid').innerHTML` delimiter. This is a fixture failure, not evidence of SAVE corruption; no assertion was weakened.
- Structurally different check: existing `tests/system/save_continue_lifecycle.py` ran in Chromium through a private local HTTP server: 25 assertions PASS, covering cold title, NEW GAME, CONTINUE, exact save restoration, one-time rewards, malformed SAVE read-only behavior, load race cancellation, input ownership, viewport rotation and dialogue/scene cancellation. This is browser emulation, not Android hardware QA. Initial sandbox socket denial is recorded in browser/initial-sandbox-denial.txt; escalated run succeeded.
- `python3 -m unittest discover -s tools/map_blender/ai_guard -p 'test_*.py' -v`: 8 tests PASS.
- Independently recomputed all 20 STORY asset SHA-256 values: 20 match reported values. This validates reported bytes, not artistic/canon concordance.
- Independently hashed 2,304 tracked PNG/JPG/JPEG files: no approved world image SHA match. Root additionally searched 2,470 local images; see `source-binary-search-20261116.json`.
- Independently generated a Blender 4.3.2 fixture and ran safe renderer with producer baseline proposal. Exit 0, source SHA unchanged, 96×96 RGBA PNG decoded and visually inspected (plain lit cube). Producer baseline/corrected PNG hashes independently match reports, measured RGB change ~2.65. Independent render pixels exactly match producer baseline, while PNG byte hashes differ. Byte-for-byte deterministic export is not established. Technical fixture only; no final art acceptance.

## Findings and gates
| Gate | Status | Reason |
| --- | --- | --- |
| G1 | BLOCKED | Exact approved world PNG absent; no direct new-map/CG visual comparison. Private current-main canon retrieval is confirmed by coordinator, not reclassified as inaccessible. |
| G2 | NOT_RUN | No finished new-world art package reviewed. Cube fixture does not qualify. |
| G3 full world | NOT_RUN | Pipeline subset succeeds; world mesh/UV/material/collision/LOD/license/budgets not verified. |
| G4 full world | BLOCKED | Existing game regression subset passes, but new spatial contract/adapter not approved or implemented; physical Android NOT_RUN. |

`tools/map_blender/lind_spatial_assemble.py` still hardcodes superseded `83dd4ad1…` source and `units_per_world_px`; it cannot serve the adopted new-map interface. `.github/workflows/lind-blender-integration.yml` uses unpinned apt Blender (version recording alone is not a pin). Both independently confirmed by reading source. No production integration should use this legacy geometry contract.

GitHub run metadata is coordinator evidence in `github-snapshot-20261116.json`. Remote ZIP download was blocked; this reviewer did not inspect remote artifact content. No main merge, publication, formal asset replacement or G1–G4 overall PASS is asserted.
