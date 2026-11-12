# MORWEN-BLENDER-26 | Two-attempt failure analysis and alternative

## Runs
- 43325328577: Blender mesh build PASS; render/export stage aborts because `libEGL.so.1` is absent. CI FAIL.
- 43326317253: EGL failure resolved, mesh build PASS, Blender reaches glTF exporter; export raises `ModuleNotFoundError: No module named 'numpy'`. CI FAIL.
- BLENDER-01 regression on second commit: PASS.

## Structural root cause
Ubuntu apt-installed Blender 4.0.2 is coupled to its system Python and OpenGL runtime, but the runner package set is not verified for render/export. A successful `blender --python` topology job does not imply graphics and glTF export dependencies are installed.

## Two-attempt limit
Do **not** make another near-identical retry by adding one more package to the existing workflow. Stop and replace the environment strategy.

## Alternative pipeline
1. Create a pinned Blender runtime (container image digest or verified Blender distribution + explicitly provisioned graphics and Python packages), with a single preflight: `import numpy`, `bpy.ops.export_scene.gltf` exists, EGL/GL availability, Blender version.
2. Split **render** and **GLB export** into independently reported steps. Preserve five rendered PNGs even if GLB export fails using `if: always()` artifact upload, and report partial success honestly.
3. Prefer software rendering in CI if headless GPU remains unreliable; validate on an actual machine before selecting the final image engine.
4. Keep canonical SHA-locked PNGs and production models untouched. Do not claim artistic QA from CI status.
5. Only after preflight succeeds, run one new environment strategy and inspect actual five-view PNGs and GLB output.

Status: `BLOCKED_ENVIRONMENT`, art QA NOT_RUN, no production merge/publication.
