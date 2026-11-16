# THE WINDBOUND OATH — Blender shared production contract

> Mandatory alongside `AGENTS.md` and `HANDOFF.md` for Claude, Codex, ChatGPT, Gemini, GitHub Actions and any Blender-executing automation. Blender itself runs scripts, not an autonomous AI agent.

## Pinned environment and reproducibility
- Verified CI base: Ubuntu 24.04, Blender 4.0.2, package version `4.0.2+dfsg-1ubuntu8`; SHA manifest: `tools/map_blender/lind/blender-ubuntu24.04.sha256`.
- Working source-review CI: `.github/workflows/lind-source-review.yml`, run #43848242090.
- Source image: PR #344 pinned commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`; expected SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.
- Pin dependencies, camera, render engine, resolution, color management, seed, input/output hashes and code commit per render. No unstated AI API or external network dependency.

## Collection ownership
`LIND_TERRAIN` WORLD; `LIND_WATER` WORLD with ECO embellishment via separate subcollections; `LIND_ROADS` WORLD; `LIND_HERO_HOME` HOME; `LIND_BUILDINGS` BUILD; `LIND_ECOLOGY` ECO; `LIND_STORY_MARKERS` INTEGRATION. Keep independently editable and retain source provenance.

## Scene and visual constraints
- Official illustration is a visual/geographic reference, NOT a metric map. No inferred meters or pixel-to-meter scale.
- Separate western/northwestern ocean cliff, eastern river raid cliff and southwest fishing inlet. Eastern story jump is directional; southeast landing is distinct.
- Do not treat 11 unplaced semantic empties or primitive blockout as final game art.
- High-quality authored silhouette, material, normal/AO bakes, LOD and baked lighting where appropriate; never copy proprietary meshes/textures from benchmark games.
- Existing game runtime uses DOM camera transform and JSON height/collision; new 3D source needs an explicit projection/export adapter and mobile QA before runtime integration.

## Required output evidence
`manifest.json`: source hashes, Blender version, script/commit SHA, seed, material references/licenses, camera, render settings, artifact hashes.
`scene.blend`: reopenable packed/linked source with explicit missing-dependency report.
`renders/`: wide scene, hero house, west cliff, east river cliff, harbor, north farmland, southeast landing, final display-size crops as relevant.
`qa.json`: technical checks and G1–G4 states with evidence paths.
Failure ledger: root cause, method family, effective attempts, changed mechanism and next hypothesis.

## Quality gates
G1 canonical alignment (BLOCKED if private canon/metrics inaccessible); G2 independent art review; G3 geometry/material/alpha/render/manifest QA; G4 runtime integration, performance and Android device QA. All must PASS for formal adoption.
After two effective failures of the same method for the same root cause, stop that method, diagnose and change mechanism. Never reset by renaming, prompt edits or branch switches.

## GitHub Actions responsibilities
- Read-only checkout and pinned dependencies, least-privilege token, no secret output.
- Source hash verification BEFORE executing Blender.
- Blender `--background --factory-startup --disable-autoexec --python-exit-code 1 --python script.py` with `set -o pipefail` when piping logs.
- Reopen saved .blend in a separate process, assert collections/objects/image bytes; save logs and hashes to artifacts.
- Distinguish source-review checks from actual production geometry and render tests.
- Actions must not merge, publish or mutate canonical files. Do not automatically mark G2 PASS.

## Entry points
`python3 tools/map_blender/validate_lind_new_world_topology.py`
`python3 -m unittest discover -s tests -p 'test_lind_new_world_topology.py' -v`
`blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python tools/map_blender/build_lind_source_review.py -- --image /path/to/verified/original.png --output /tmp/lind-source-review.blend`
These commands verify source-review infrastructure only, not completed terrain.
