# HAIRHARPY-EVAL-01 — candidate tool assessment (2026-11-16)

Status: **EVALUATED / NOT INSTALLED / NOT INTEGRATED**. This document does not approve new canonical assets or external executables.

## Upstream
- Official: https://github.com/Rackta/HairHarpy
- Building: https://github.com/Rackta/HairHarpy/blob/main/BUILDING.md
- License: https://github.com/Rackta/HairHarpy/blob/main/LICENSE.md
- Author's detailed manual: https://boosty.to/catarackta/posts/d65c1894-2cab-4be3-b45a-6411710c3cc9

HairHarpy v2.0 is a **standalone Windows/Linux Vulkan GUI application**, not a Blender Python addon. It creates volumetric stylized hair from curves/NURBS and can export OBJ/FBX/glTF; Blender bridge is described upstream. The Linux build uses CMake, Qt 6.8.3 and a Vulkan driver; upstream has an Ubuntu 22.04 GitHub Actions build. This supports a possible **build** in CI but does not establish reliable **headless hairstyle editing** in a stock GitHub Actions runner.

## Licensing and security gate
HairHarpy Source-Available License 1.0 allows local source builds, commercial use and use of produced meshes. It prohibits redistributing source/binaries or incorporating them in another product without written permission. Do not vendor the code, package a compiled executable in game Artifacts, or upload an executable to this repository. Keep only upstream links, instructions, and independently produced game assets. A personal-use source build in ephemeral CI may be technically feasible, but verify compliance and avoid distribution. Releases are unsigned; verify the publisher's SHA256SUMS and inspect third-party dependencies before any execution. Do not automatically execute an unreviewed release installer.

## Proposed workflow (requires feasibility QA)
1. Locate official approved Morwen reference binaries and verify SHA256; G1 currently BLOCKED. Preserve deliberate left/right asymmetry.
2. Independently evaluate HairHarpy using **non-canonical test hair** on a compatible GUI/Vulkan environment, including export and Blender import. No modification to official model.
3. Verify mesh topology, UVs, normals, silhouette and licensing provenance; record tool version, SHA, export settings and deterministic build information.
4. If export succeeds, use the candidate mesh in a separate Blender scene for 4-direction and 3/4 renders, then evaluate 48px game-size and rig deformation.
5. If GUI/Vulkan cannot be provided through GitHub Actions, do not claim CI integration; use Blender Python/Geometry Nodes or an explicitly user-approved remote desktop workflow instead.

## Quality gate
G1 canonical source: BLOCKED; G2 visual match: NOT_RUN; G3 actual HairHarpy build/export/import: NOT_RUN; G4 game/Android: NOT_RUN. Existing EYELID-09 lash/cage G3 FAIL (123 triangle intersections) remains a separate issue; hair software is not an eyelid collision fix.

## Decision
**Conditional candidate adoption for Morwen hair**, not installation. Do not attempt commercial use of third-party sample models without checking their separate asset licenses. Do not modify main, published assets or approved binaries.
