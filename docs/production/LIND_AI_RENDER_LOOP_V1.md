# LIND-AI-LOOP-01 — controlled render/feedback/re-render protocol

Status: bounded technical implementation; **not** autonomous artistic approval.

## Security boundary
- AI feedback is **untrusted data**. Never execute AI-supplied Python, shell commands, file paths, node names, or arbitrary Blender expressions.
- Parent runner holds any AI credential. Launch Blender with an explicit minimal environment allowlist; never inherit API keys, GitHub tokens, credentials, or cloud config into child Blender process. Restrict network at runner/container level when available.
- AI proposes JSON only; `tools/map_blender/ai_guard/validate_patch.py` validates strict schema, exactly one known asset ID, max three permitted numeric adjustments, finite values and clamping. Unknown fields rejected.
- Blender consumer reads only normalized JSON and maps keys to pre-approved scene properties. No arbitrary geometry mutation, deletion, asset overwrite, save-game access, canon adoption or main merge.
- Write every output to a new candidate directory, not the source tree. Before and after, hash canonical source assets. A candidate must never be marked formally adopted by automation.
- No AI API dependency for technical validation. Visual AI is optional and only if explicitly connected and authorized; absent vision, independent G2 stays NOT_RUN/BLOCKED, never PASS.
- Same root cause + method family: stop after two failed render-and-review corrections. Keep cumulative ledger and switch structurally different methods; do not reset by renaming.

## Allowed adjustments (v1)
`light_energy_multiplier` [0.8,1.2]; `light_size_multiplier` [0.9,1.1]; `camera_ortho_multiplier` [0.95,1.05]; `exposure_delta` [-0.2,0.2]; `roughness_delta` [-0.05,0.05].
Only additive/relative lookdev tweaks; no geometry topology or spatial coordinates. Normalization clamps out-of-range finite numbers. Values cannot override locked scene values outside a separately approved adjustment pass.

## Pipeline
1. Source SHA, official references and manifest check; G1 BLOCKED if unavailable.
2. Render source in isolated Blender process; capture .blend candidate, full view, 48/96px previews, logs and hashes.
3. Technical QA: hashes, camera, geometry counts, transparency, render outputs. Human or image-capable GPT independently inspects actual PNG; no unsupported art PASS.
4. Write feedback JSON and bounded correction proposal with root-cause and method-family IDs.
5. Validate/normalize proposal; apply only allowlisted values in a separate non-destructive render. Save before/after image comparison and test results.
6. If QA fails twice for same cause/method, stop that method; report failure and redesign. Save candidate evidence to GitHub Actions artifact; commit code only to dedicated branch/Draft PR.
7. Final adoption requires G1–G4 PASS and explicit director approval; no automated main merge/publish.

## Test scope
Validator unit tests: valid proposal, numeric clamp, unknown code injection, geometry deletion request, nonfinite value, excessive keys. This does not establish end-to-end Blender render success or independent G2 art quality.

## Remaining engineering before full automatic cycle
- Safe Blender property adapter restricted to named scene objects and expected types.
- Child process launcher with sanitized environment and resource limits.
- Existing Blender workflow integration, image inspection adapter and reviewer handoff.
- GitHub Actions artifact/PR evidence, no secrets in logs.
- Actual end-to-end render, compare and Android validation.
