# 3DNCHU TECHNIQUE WATCH — 2026-11-16

Status: **RESEARCH / CANDIDATE METHODS ONLY**. No third-party software installed, no source binaries redistributed, no canonical art modified.

Research source: https://3dnchu.com/ (editorial index, not authoritative software licensing).

## Prioritized for THE WINDBOUND OATH

| Candidate | Editorial source | Target | Validation before use |
|---|---|---|---|
| Hair Wrangler (Blender Geometry Nodes/curves) | https://3dnchu.com/archives/hair-wrangler-for-blender/ | Morwen bob hair clump silhouette | Official license, supported Blender version, unattended execution, mesh export, four-view art QA |
| Stylized Hair PRO | https://3dnchu.com/archives/stylized-hair-pro-v3-2/ | stylized layered hair | License/cost, Blender compatibility, silhouette QA; do not purchase without approval |
| Geometry Nodes normal transfer | https://3dnchu.com/archives/transfer-normal-use-geometry-nodes-narita-haruka/ | stylized face/hair shading continuity | Reimplement using built-in Blender nodes on disposable candidate; compare normal orientation and rendering |
| Facial Hair Toolkit 2.0 | https://3dnchu.com/archives/facial-hair-toolkit-2-0/ | hair cards/texture bake | Paid plugin; no purchase or download without explicit approval |
| Floaters technique | https://3dnchu.com/ homepage article dated 2026-11-14 | architecture ornaments, armor details | independent mesh/decal tests, camera distance, z-fighting, normal QA |
| mPainter alpha / CG Painter alpha | https://3dnchu.com/ homepage entries 2026-11-12 / 2026-11-05 | layered PBR texture authoring | alpha stability, supported file formats, headless feasibility, license; no production adoption based on preview |
| Raster to Pixel | https://3dnchu.com/ homepage entry 2026-11-12 | sprite downscale/palette QA | compare actual 32/40/48px rendering and transparency, avoid uncontrolled automatic redesign |

## Implementation policy
1. Prefer **built-in Blender methods** where equivalent quality can be achieved, particularly Geometry Nodes normals, curve-based clumps, procedural UV and bake; they can run in existing GitHub Actions without unreviewed third-party binaries.
2. For external tools, read original upstream documentation, verify license and version, and perform an isolated test. The editorial article is a discovery source, not installation authorization or a verified license.
3. Avoid simultaneous competing hair tools; evaluate one candidate against the official Morwen reference after exact image SHA verification. Preserve intentional left/right asymmetry.
4. Compare against current approved asset with 4-direction and 3/4 renders, 48px game display, deformation and performance. Retain scripts, inputs, seed, SHA and tool versions.
5. G1 exact approved imagery is still **BLOCKED**; EYELID-09 existing lash surface collision **G3 FAIL** (123 pairs). New hair tools do not resolve eyelid geometry intersections.

## Execution
This is a **non-destructive technique selection and validation plan**, not an installation, Blender build, new rendered asset, or QA PASS. Next low-risk action: independent Blender Geometry Nodes normal-transfer test on disposable hair clumps, with explicit input/expected-output tests, then compare visual QA before proposing production use.
