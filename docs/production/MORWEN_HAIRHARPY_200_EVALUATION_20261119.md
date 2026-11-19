# Morwen HairHarpy v2.0.0 evaluation — 2026-11-19

**Status:** EVALUATION / NOT INSTALLED / NOT AN ADOPTED ASSET. Existing Draft PR #427; no main merge or official design change.

## Upstream and provenance
- Publisher: Rackta / CataRackta; https://github.com/Rackta/HairHarpy
- Release: https://github.com/Rackta/HairHarpy/releases/tag/v2.0.0
- Project release description: full desktop rewrite in C++ / Qt6 / Vulkan, formerly Stylized HairMesh Creator.
- License: **custom/source-available, NOT automatically open-source**. Author-built software is described as usable for personal/commercial projects; generated meshes remain user's work, but redistribution of software/source requires separate permission. Verify current upstream license before copying binaries or code into TWO.
- Supply chain: binaries unsigned. Compare official `SHA256SUMS-linux.txt` / `SHA256SUMS.txt` with downloaded assets; inspect `TRUST.md`. Do not execute unverified downloads.
- Linux prerequisites: Vulkan 1.1, glibc >= 2.35, X11 or XWayland. AppImage/tar.gz available. Windows 10/11 x64 portable/installer.
- Official trust notes: https://github.com/Rackta/HairHarpy/blob/main/TRUST.md
- Secondary overview: https://3dnchu.com/ (2026-11-16 HairHarpy v2.0.0 report).

## Artistic application to Morwen
1. Use approved Layer 0 four-angle reference to design a short bob with layered fringe, temple locks, and staggered nape tips. Never treat a generic HairHarpy preset as the official design.
2. Prefer Hair Room's curve-controlled **surface clumps**, crown/side controls, symmetry, and collision capsule to previous failed Blender Bezier tube / repeated primitive clumps. Distinguish NURBS surface clumps from bevel-tube strands.
3. Topology Room: retopo and edge flow, UVs (editor reported early/test stage), inspect normals, root attachment, self-intersections, hairline, scalp occlusion.
4. Export an independent **candidate** mesh (OBJ/FBX/glTF as supported), import into Blender 5.2.4 and optionally 5.3 in separate evaluation. Check actual transform, units, material, normals, UV, face count, manifold suitability, render and glTF/Android performance.
5. Compare front/right/back/left and three-quarter with official images, final display-size silhouette, hair-tip thickness and shading. G2 requires independent art QA.

## Environment decision
- GitHub-hosted Ubuntu Actions typically lacks the graphical Vulkan/X11 session HairHarpy expects. Do not attempt uncontrolled AppImage execution in ordinary headless CI or claim successful installation.
- Preferred near-term use: research its source/bridges and export format, perform a **small isolated compatibility experiment** only on a proven graphical Vulkan-capable runner or approved workstation.
- No paid API, no source redistribution, no unreviewed third-party bridge installation, no overriding Blender 5.2.4. Blender 5.3 remains separately evaluated.
- Keep sculpting face and head in Blender in parallel; HairHarpy is a hair-production option, **not a blocker for actual sculpt progress**.

## Acceptance / stop criteria
- Technical PASS: verified source SHA, provenance/license, installed executable on suitable machine, export/import, actual Blender render, geometry/UV/normals checks, project-file preservation.
- Artistic PASS: official four-angle design match, clean hair silhouette, believable layered clumps, scalp/root continuity, no intersections at motion extremes, independent art reviewer.
- Stop: Vulkan unavailable, unacceptable license/security, inability to export a reusable mesh, or two failed tests with the same root cause. Switch to native Blender manual sculpt/retopo rather than re-running equivalent failed setup.
- **Current gates:** software discovery PASS; installation NOT_RUN; Blender bridge NOT_RUN; actual hair model NOT_RUN; G1/G2/G3/G4 NOT_RUN for HairHarpy candidate.

## Next independent executable work
Check exact official Linux release hashes and `TRUST.md` source, review bridge files statically, and record export schema. Do not require the user's Android phone to run desktop software. Continue Blender voxel head artifact QA separately.
