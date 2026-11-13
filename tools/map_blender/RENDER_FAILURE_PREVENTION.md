# BLENDER RENDERING FAILURE PREVENTION v1.0
Scope: tools/map_blender and GitHub Actions map-blender-08-preview.yml
Status: automated technical gates implemented; independent visual QA remains mandatory.

## Root cause and prevention
Incident 2026-11-13: Blender 4.0.2 on ubuntu-24.04 reported 'Build without OpenImageDenoiser'; hero roof Cycles render failed.
- Explicitly disable Cycles render and view-layer denoising until an OIDN-capable build is verified.
- Run a real 32x32 Cycles render (blender_preflight.py) before expensive MAP jobs. Syntax checking is insufficient.
- Verify SHA-256 and nonempty artifacts for hero tile and prior MAP checks.
- Upload partial outputs on failure; report failure as failure.
- After two identical failures stop retrying, analyze logs, switch renderer/build or approach.

## Release gates
1. Syntax and topology PASS.
2. Cycles preflight render PASS.
3. Production PNG/BLEND generation PASS.
4. SHA256 and file size verification PASS.
5. Independent visual QA PASS before asset adoption.
6. Runtime/Android QA PASS before main merge.

## Limitations
- Preflight cannot guarantee zero later failures (OOM, script logic, transient CI).
- MAP08-MAP23 still run as one long workflow; isolate future jobs to reduce waste.
- Never mark art or Android QA PASS based on CI alone.
