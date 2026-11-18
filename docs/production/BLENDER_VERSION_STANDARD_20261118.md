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
- Current 5.2.4 qualification workflow: `.github/workflows/two-blender-524-qualification.yml`, PR/push-triggered execution verified in run 44287739095.

**Status:** runtime PASS (2026-11-18; see verification below); branch ownership consolidation PARTIAL; G1/G2/G3/G4 new production NOT_RUN. **NO-GO for new character/map modeling.** No main merge or original replacement.

## Verified runtime qualification — 2026-11-18
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44287739095
- Commit: `f8ec6712ee293987cf6ea2cd27944a1d1206bc18`; branch: `feature/morwen-rebuild-01` (Draft PR #419).
- Official `mirror.blender.org` SHA-256 manifest download, archive verification, Blender 5.2.4 LTS startup, isolated temporary `.blend` save/reopen, and evidence upload: **PASS**.
- Runtime output: `TWO_BLENDER_524_RUNTIME_PASS`; reopen output: `SMOKE_REOPEN_PASS`; scene audit `version_pass=true`, `source_opened=true`, `meshes=2`, `missing_external_images=[]`.
- Artifact: `two-blender-524-runtime-smoke`, ID `14418778908`, expires 2026-12-02; artifact ZIP digest `sha256:af619bd07efb1e203885cdbf08b0bc3fdced1760cd36ba42cf4856ef991aa298`.
- Initial `download.blender.org` HTTP 403 in run 44280556396 was resolved by one official-mirror change. No further retries required.
- **Scope:** This qualifies Blender 5.2.4 as an executable shared CI runtime. It does NOT qualify actual game character/map art, materials, rig, traversal, WebGL/Android performance, or legacy compatibility (not required).
- **Decision:** Runtime gate PASS. New 3D geometry production remains NO-GO pending explicit director resume and other relevant readiness/QA gates.

## Shared installer integration QA — 2026-11-18
- Canonical installer: `tools/production_qa/install_blender_524.sh` (read-only with respect to repository and system packages).
- Existing qualification workflow calls canonical installer: `.github/workflows/two-blender-524-qualification.yml`.
- PASS: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44289286470 (commit `9f7582823f0c45fb0f3982b523b201afa8c9c194`).
- All qualification steps succeeded, including upstream checksum verification, Blender launch, temporary `.blend` save/reopen and evidence upload.
- Artifact: `two-blender-524-runtime-smoke`, ID `14420437768`, expires 2026-12-02, zip SHA-256 `828efcd96dee8b896a6f1eaf0af01addf1c08b097f71c23d2285bdbf9ddd64dc`.
- Existing character/map workflows are NOT automatically migrated; apply installer only to workflows selected for active new production. Legacy asset compatibility is explicitly out of scope.
- Runtime/installer QA PASS does not constitute G1–G4 production asset approval or authorize restarting modeling.

## Full open-PR inventory evidence — 2026-11-18
- Read-only GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44290316165 (PASS).
- API pagination inventory: **202 open PRs**. Heuristic labels: **LIND 70**, **Morwen 75**. These categories are not necessarily disjoint and are NOT verified duplicate counts.
- Artifact `two-production-pr-inventory`, ID `14421276223`, ZIP SHA-256 `0b54b5d31d910ce98ebaafea2f2fe5a6dd8a90b8fe5fb5cfc8b67dff676e69e6`, expires 2026-12-02.
- No PR closures, merges, deletions or main modifications. Prioritize human-reviewed reuse and ownership assignment; avoid automated cleanup based solely on keywords.
