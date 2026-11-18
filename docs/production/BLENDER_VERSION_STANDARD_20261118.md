# TWO — Blender common new-production runtime candidate (2026-11-18)

**Director scope revision:** BOTH character and environment assets will be rebuilt. **Do not test old candidate .blend compatibility as a prerequisite to resuming production.** Preserve old files and QA/failed-method records as reference evidence, but do not migrate or repair old topology merely for backward compatibility.

## Version decision
- Blender **5.2.4 LTS** is the selected *candidate* for one common character/map production runtime; installation and execution are NOT_RUN. Do not call it operational until a real GitHub Actions run succeeds.
- Version pin + official SHA-256 archive verification required. No unverified apt fallback. One bounded install attempt per distinct root cause, stop repeated failed method.
- Other versions may open legacy files only when there is a specific recovery need, **not** as a migration gate.

## Minimum effective environment gates
1. **Runtime:** GitHub Actions starts exact Blender 5.2.4 and verifies version, SHA-256, an isolated throwaway .blend save/reopen, logs and downloadable artifact. Smoke cube is ONLY a technical test, not an asset.
2. **Source-of-truth:** current canon four-angle character references, official environment CG/world setting, SHA manifest and licenses available to both teams. Protect originals.
3. **Production ownership:** map and character separate owners, shared camera/scale/ground/lighting/export interface; one active PR per asset-stage owner, reuse existing branches.
4. **Quality:** independent G1 design, G2 actual sculpt/material, G3 geometry/UV/rig/technical, G4 WebGL/Android; no preemptive PASS.
5. **Game targets:** define and test final display scale, scene lighting, glTF pipeline, memory/draw calls, Android performance on NEW assets. Do not run legacy compatibility sweeps.
6. **Method:** art-directed sculpt and retopo for characters, Art-Directed Hybrid World Production for environment; preserve previous failed-method ledger. New geometry creation remains paused until director's explicit resume decision.

## Explicitly removed from readiness checklist
- Bulk reopening of PR #316/#318/#399/#407 old .blend candidates.
- Re-rendering or GLB exporting legacy character/map candidates solely to prove 5.2.4 backward compatibility.
- Retrofitting old rig, UV, Geometry Nodes or shaders solely for migration.
- Generating more planning documents, duplicate branches, or repeated failed install attempts without causal change.

## Existing failure context
- LIND run 44233677269 failed APT dependency mirror HTTP 404, not a modeling error.
- Previous Morwen official tarball HTTP 530 is a different acquisition failure.
- Current 5.2.4 qualification workflow: `.github/workflows/two-blender-524-qualification.yml`, manual dispatch, not yet observed running.

**Status:** runtime NOT_RUN; branch ownership consolidation PARTIAL; G1/G2/G3/G4 new production NOT_RUN. **NO-GO for new character/map modeling.** No main merge or original replacement.
