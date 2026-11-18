# TWO — Blender common production version candidate (2026-11-18)

**Candidate: Blender 5.2.4 LTS. NOT YET VERIFIED AS PRODUCTION RUNTIME.** Director requested one more effective common version. Adoption requires runtime and original-asset QA.

## Selection
- 5.2.4 LTS: official long-term support until July 2028; strong fit for character and environment Geometry Nodes workflows. https://www.blender.org/releases/5-2/
- 5.3.0: newest feature release, research-only until compatibility demonstrated. https://www.blender.org/releases/5-3/
- 4.5.16 LTS: fallback if 5.2.4 fails a relevant compatibility gate. https://www.blender.org/releases/4-5/
- 4.3.2 / 4.0.2: legacy read-only checks; not new production standard.

## Installation and acceptance
1. Download official 5.2.4 Linux x64 archive and published SHA256; verify full archive digest before extraction; do not invent digest or silently use apt version.
2. Cache by exact version + verified SHA; bounded download attempts, stop on same failure cause.
3. Run `blender -b --factory-startup --python-expr 'import bpy; assert bpy.app.version==(5,2,4)'` on Ubuntu 24.04 Actions.
4. Open recovered original .blend files read-only, collect mesh/UV/shapekey/rig/material/external texture inventory via `tools/production_qa/validate_blender_runtime.py`; compare with SHA-locked originals. Do not resave originals.
5. Render four angles from one actual character and one environment candidate. Verify GLB export/reimport, material and Geometry Nodes regressions. Android/WebGL is a separate G4 test.
6. Independent G2 art QA; G1 official references/licenses, G3 source reopen, G4 real device QA recorded independently. Only after these gates pass, promote to formal common production standard.
7. Update only existing active workflows in their own established branches after evidence; no mass edits or new PRs.

## Failure distinctions
LIND run 44233677269: apt mirror dependency 404; earlier Morwen 4.3.2 download 530: different failure. Neither is a 5.2.4 incompatibility finding.

## State
Version policy candidate documented; actual Blender 5.2.4 acquisition, reopening, rendering and Android tests NOT_RUN. New sculpt/map modeling remains NO-GO.
