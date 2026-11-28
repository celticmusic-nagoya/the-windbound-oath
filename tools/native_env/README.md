# Native environment qualification slice (infra, calibration fixture only)

Owner: Claude (this branch). Shared engine/CI/lease remain #468 (Codex). No asset, canon, lease or main writes.
Every native edit here is on `CAL-*` calibration objects; nothing is a TWO asset or candidate.

| File | Role |
|---|---|
| `native_stages.py` | Blender stage executor: build, measured control-response calibration, blueprint-target correction, PBR/GN material correction, preview/HQ render, reopen measurement |
| `pbr_factory.py` | Shared procedural PBR node group `TWO_PBR_Factory` + Geometry Nodes `TWO_GN_Scatter` (5.3 modifier-input API with legacy fallback) |
| `render_views.py` | Shared matched rig (front/right/back/left/three-quarter), preview (Workbench clay+wire, Cycles 16 spp) and HQ (Cycles 128 spp, OIDN) |
| `native_session_adapter.py` | Long-session adapter on pinned #468 `session_plan.ready` + `bounded_operation.run_operation` (SHA-verified); checkpoint/promote/quarantine, independent-process reopen, ledger + SHA256SUMS, run1/run2 |
| `fetch_restore.py` | Cross-run restore through the shared hash-verifying artifact downloader, safe extraction, SHA256SUMS check |
| `hairharpy_runtime.sh`, `hairharpy_bridge_probe.py` | HairHarpy v2.0.0 official asset/SHA, tag source identity, Linux runtime (Xvfb + lavapipe Vulkan), Blender 5.3.0 bridge |

run1 = push without `restore_request.json`; run2 = commit `restore_request.json` (`source_run_id`, `source_head_sha`, `artifact_name`).

Readiness (Continuity policy labels) is reported per revision in PR comments, not here.
Interface for owners: an asset adapter supplies stage callables with the same contract (`--out`, `--report`, metrics with
`output_sha256`) and its own measurable blueprint metrics; it must be qualified on the owner's disposable native copy.
