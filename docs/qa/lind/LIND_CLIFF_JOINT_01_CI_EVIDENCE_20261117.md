# LIND CLIFF-JOINT-01 — CI evidence and gate review

Commit `d559de340954c0b416db829011e02b8b39b49059`.
Successful Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43988312919
Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43988312919/artifacts/14286377065
Artifact ZIP reported size: 1,798,597 bytes, 6 uploaded files; upload digest `f0625a8e4068832554c04ef711b970278756f6e6e07ea8b52b504ca339f8339a`.

## Verified in Actions logs
- Ubuntu 24.04, Blender 4.0.2.
- Blender execution and three clay render steps: success.
- Python verified PNG signatures, SHA-256 of 3 PNGs and saved .blend; success.
- Blender reopened saved .blend and asserted at least 30 `GEO_JOINT_` objects; `REOPEN_OK`.
- Upload step success; actual ZIP contents not separately decoded in this audit.

## Earlier failure and repair
Run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43987996444 failed before geometry because `libEGL.so.1` missing. Commit `d559de3` installed EGL/GL runtime and added preflight; subsequent run succeeded. This is one environmental root-cause repair, not a geological G2 retry.

## Important limits
- Current geometry is irregular planar Voronoi fracture-cell outcrop and continuous turf surface, **not yet sculpted photoreal Irish geology**.
- No independent visual inspection of rendered PNGs in this audit, no screenshot claim, no source CG registration in generated .blend, no approved spatial dimensions or road-support proof.
- This study should not be promoted to final map; independent three-view image inspection and final-size comparison required before photo-PBR application.
- Bridge/stone work remains Codex-owned; no production runtime changes.

## Gates
- G1 full world/source alignment: BLOCKED (source hash is a reference declaration, not image packed into study).
- G2 art: NOT_RUN (do not infer PASS from three successful renders).
- G3 limited Blender execution, PNG signatures/hashes, blend reopen: PASS. Complete geometric/UV/nav/collision G3: NOT_RUN.
- G4 game/Android: NOT_RUN.
