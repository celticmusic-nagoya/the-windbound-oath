# LIND coastal cliff source 04 — real scan render and independent QA (2026-11-17)

## Execution and real source evidence
- Draft PR #369; workflow run [43991664085](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43991664085), all jobs PASS.
- [Artifact 14287347754](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43991664085/artifacts/14287347754): 95,041,154-byte ZIP with original verified glTF + binary + three 1K textures, packed saved Blender file, 5 PNGs, source/render manifests and logs. **Do not mistake ZIP compression size for uncompressed source size.**
- Exact publisher asset: https://polyhaven.com/a/coastal_cliff_04 ; publisher source license: https://polyhaven.com/license (CC0). No verified Irish photographic location. Official GLTF source SHA-256 `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`; .bin SHA-256 `f7c3a18acc848552b91b0de931ba8439d5f2a8849bd0d4ac718878aa4a90abcf`. Publisher manifest size and MD5 all matched.
- Blender 4.0.2 imported real 3D geometry, one Blender mesh object, **1,537,926 triangles**, UV layers: 1, AABB extents 86.77198 × 24.24743 × 10.99971 units (unit basis is file metadata, not an approved LIND transform); saved and reopened packed `.blend`. Independent artifact re-extraction confirmed render hashes on 5 actual PNGs.

## Independent visual assessment of actual images
- Front, oblique and reverse scans show genuinely irregular eroded fractures and non-periodic surface relief. This **materially improves** over the artificial waves/cells of PR #367 and PR #368.
- Top: source is fragmented into detached-looking pieces and exposed back sides. A source visual scan may contain gaps/isolated rocks, but this is not a naturally joined village cliff or continuous terrain cap.
- Silhouette: very long and narrow cut-out rock strip with visible abrupt source boundaries. No seamless soil/turf interface, river/coast contact, approved placement, shadow integration or game scale established.
- PBR image uses the actual provider maps but reads too dark and at distant framing; cannot judge close-up material quality at final game size.
- Source may be considered for **surface dressing / rock outcrops** on a separately authored, coherent world terrain; do not directly substitute it for the game's complete cliff or collision geometry.

## Independent GLTF topology audit
An independent script parsed the binary glTF primitive position/index accessors directly from the verified original artifact (not from rendered images). It computed connected components by undirected triangle adjacency and edge incidence across all indexed triangles:
- Raw indexed-vertex graph: 789,032 source vertices; 1,537,926 indexed triangles; **143 index-connected components** and **39,894 one-face indexed edges**. This overcounts physical gaps because UV seams duplicate vertex positions; do NOT describe these 143 components as 143 physically detached rocks.
- After **exact-position welding** (771,255 unique positions, no tolerance needed), geometry has **3 spatially connected components**, containing 1,378,010 (89.60%), 103,342 (6.72%) and 56,574 (3.68%) triangles.
- Welded geometric edge incidence: **4,578 open boundary edges**; zero edges incident to >2 faces; zero triangles collapsed by welding. Quantized welding at 1e-5 and 1e-4 gave the same counts.
- The scanned formation is therefore mostly contiguous geometry but **not watertight**, with two additional disconnected groups and open cut/scan boundaries. It is an excellent source candidate for rock-surface dressing; a directly collidable unified map still requires authored continuity, topology treatment and independent collision/nav QA.
- Both audits operated on the same verified glTF source binary, and full geometric self-intersection/volume tests remain NOT_RUN.

## QA gates (finished LIND map requirement)
- G1 **BLOCKED**: source hashes/license provenance checked, but official CG/approved scale/placement/Irish geography alignment not checked.
- G2 **FAIL for final map adoption**: realistic raw cliff *source*, but disconnected strip, visible source edges, unintegrated soil/water and dark wide PBR view; art value as an unadopted candidate retained.
- G3 **FAIL for final game-ready cliff**: scan import/renders/hashes/reopen PASS; open topology and disconnected pieces reject a directly collidable map. UV/PBR render succeeds, game mesh LOD/navmesh collision NOT_RUN.
- G4 **NOT_RUN**: no game/Android integration/performance or game-size visual checks.

## Scope and next eligible production operation
Preserve original GLTF/texture bytes and hashes. Do not recursively repeat failed Voronoi, sinusoidal or bridge Boolean carving.
1. Construct an independently authored **continuous macro cliff and world terrain collision volume**, using approved map/CG alignment before deciding final transforms.
2. Fit selected scanned rock patches as **surface-dressing or overhang modules**, without destructive Boolean division of either the source or Codex bridge stones; validate layer seams/occlusion.
3. Test at correct final viewport scale and separate 1K-preview from 2K/4K final textures and normals. Decimate/retopologize surface pieces only after preserving high-quality geometry and screenshot comparison.
4. Obtain four gate PASS before formal adoption. PR #363 bridge masonry remains Codex-owned, G2/G3 FAIL, and unchanged.

No original source, bridge geometry, approved CG, main or public game file was changed by this scan investigation.
