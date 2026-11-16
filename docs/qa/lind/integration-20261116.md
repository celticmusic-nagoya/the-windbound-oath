# LIND-RENDER-01 technical execution evidence — 2026-11-16

Executor: Codex INTEGRATION sub-agent. Producer self-QA, not independent approval. Baseline `c0223b538c3a8b20329ea847c7237b424ccfac4a`. No production assets/game code modified. Exact runtime version: Blender 4.3.2, Debian 13.6.

## Executed

- Read AGENTS.md, causal retry v2, adopted master, parallel team plan and workboard.
- `python3 -m unittest discover -s tools/map_blender/ai_guard -p 'test_*.py' -v`: 8 tests PASS (includes mocked environment/source protection tests; this alone is not a render).
- Created a new isolated technical fixture via existing `create_fixture.py` in `/tmp/lind-integration-20261116/fixture.blend`.
- Executed existing `run_blender_safe.py` twice against this same fixture, baseline exposure 0 and corrected exposure +0.1; both actual Blender processes exited 0. Source hash remained unchanged.
- Decoded both 96×96 RGBA PNGs with Pillow; nonempty pixel difference verified. Visually inspected baseline: a technical cube fixture only. Evidence reports include source/proposal/normalized-patch/render SHA and process log tails. EGL_BAD_MATCH warnings occurred; successful exit and decoded images confirmed.
- No candidate/world asset construction, adoption, release, workflow rerun, full-world G3, Android/device check or runtime integration was performed.

Coordinator evidence: [GitHub snapshot](github-snapshot-20261116.json) records the existing Actions/Artifact metadata; artifact ZIP content was not retrievable and is not counted as inspected. [Source-binary search](source-binary-search-20261116.json) records the missing exact adopted source image; no replacement was created or registered.

Machine evidence: [integration-20261116/validation.json](integration-20261116/validation.json); guard log, Blender version, normalized patches, runner reports, command logs and actual PNGs are in the same directory. The generated fixture is ephemeral; reproduce it with the committed fixture generator rather than treating it as a village asset.

## Existing pipeline findings

1. `.github/workflows/lind-blender-integration.yml` uses apt distro Blender on ubuntu-24.04 and records its version; it does **not pin a Blender version** as required for production. Tests safely upload fixture evidence and use read-only contents permissions; successful CI would remain technical fixture evidence only.
2. `tools/map_blender/lind_spatial_assemble.py` hardcodes superseded image SHA `83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c`, and requires `units_per_world_px`. It cannot implement the new adopted image/meter-based design without an explicitly reviewed replacement contract. Do not feed old pixel layout into the new world.
3. Existing assembler allows missing asset SHA, trusts caller `canon_review=PASS`, has no director spatial-lock field check and does not refuse an existing output blend. It is **not a safe approved assembly route for the new world**. Left untouched because it belongs to the shared legacy interface and no reviewed replacement exists.
4. Safe numeric render runner refuses existing output PNG/normalized patches and strips inherited credentials; `--disable-autoexec` is used. It explicitly is not an OS sandbox for untrusted blend files. Timeout path lacks a structured report/source-hash-finally check: this audit did not hit the timeout and did not alter the shared runner.
5. No complete world-package UV/normals/collision/LOD/draw-call/alpha/material-license validator or game adapter was demonstrated. Source preservation checks and image hashes are implemented for the technical render fixture.

## Candidate integration interface (proposal only)

Keep HTML/JS runtime and SAVE serialization unchanged pending separately approved integration. A future candidate package must supply immutable source/asset SHA, reviewed spatial-contract version with physical units, explicit `windward_cliffs_wnw` and `raid_riverside_cliff` anchors, stable event and door IDs, world transforms, material/license index, bounds and collision/nav data, camera and export settings, LOD budgets, deterministic seed/version and G1–G4 evidence. PNG atlas/billboard exports or glTF remain options requiring an approved adapter; no runtime switch is authorized by this report. Independent wind and water channels must preserve water flow at wind-stop.

Never assemble Claude WORLD/HOME/BUILD/ECO packages until their reviewed immutable manifests and common contract exist. No coordinates are inferred here. Approved world image registration remains blocking: expected `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.

## Gates

G1 BLOCKED (exact adopted source registration/private canon comparison handled by coordinator); G2 NOT_RUN; G3 NOT_RUN for world (isolated technical fixture render PASS only); G4 NOT_RUN. Independent QA is a separate agent. Method ledger: lighting-fixture/test-exposure executed baseline and correction, zero failures; neither is a failed art attempt and no method switch was needed.
