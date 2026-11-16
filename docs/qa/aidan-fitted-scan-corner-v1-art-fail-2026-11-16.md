# Aidan scan-derived fitted corner v1 — independent art QA (2026-11-16)

Evidence: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43786045981 ; artifact `aidan-fitted-scan-corner-v1` (id 14189994973), containing `fitted_scan_three_quarter.png`, `fitted_scan_front.png`, `fitted_scan_top.png`, `fitted_scan_audit.json`. Source is pinned Poly Haven CC0 scan `rock_moss_set_01_8k.blend`, SHA256 `23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6`.

## Result
- GitHub Actions / Blender 4.0.2 run: **PASS**; 3 images rendered; 3 separate modified scan meshes: lower_east 7436 polygons, lower_north 2897, upper_bond 9549.
- Independent visual inspection of all 3 PNGs: **G2 FAIL**. The stones are disconnected, the top stone visibly floats, lower stones are mismatched and expose a large dark void, and right-hand cut surfaces look unnaturally vertical/stepped. Composition resembles piled rocks rather than a constructed masonry corner. No PBR treatment can fix this structural defect.
- Recorded AABB: lower_east/lower_north overlap [0.036,0.42,0.6] (AABB overlap alone **does not prove mesh intersection**). Upper stone is separated by 0.15 units in Z from each lower stone. **G3 FAIL** for planned stone-bearing contact; mesh-level intersection/physical support still NOT_RUN.
- EGL initialization warnings and Blender shutdown unfreed-memory diagnostic were logged despite successful images; not automatically art or geometry failure. Record but do not mask.
- **G1 BLOCKED** for exact adopted architecture dimensions; village context verified. **G4 NOT_RUN**.

## Causal diagnosis
The v1 process independently scaled and plane-clipped raw natural boulders then placed them at manually guessed offsets. It never designed shared joint/contact surfaces or verified support against actual mesh triangles. Holes-fill operation and face-plane clipping produced visually abrupt vertical edges. The core defect is not just 0.15 Z placement: it is **lack of coupled stone-contact geometry**.

## Method switch
**Stop using independent rock clipping + arbitrary offsets as a candidate final architecture technique.** Do not count a mere height adjustment as a new method family. New proposed family: *joint-first designed masonry*:
1. Design the physical L-corner course's bearing and vertical contact planes in a shared 2D/3D joint graph, with explicit supported area and tolerances.
2. Sculpt each individual stone exterior *around the pre-established shared joints*, using CC0 scan normal/height information on exposed faces only; ensure watertight geometry after boolean/cap operations and surface continuity.
3. Measure contact and overlap with actual mesh intersection/clearance, not only AABB; include manifold and UV checks, and small-size render.
4. Keep model **noncanonical and isolated** until official house master/dimensions confirmed; require independent G2 before PBR/game integration.

This is a structural change from v1: shared fitted joints first rather than scan-boulder shape first. Do not rerun v1 with slightly adjusted transforms or pretend G2 PASS. Preserve this failed v1 evidence. No official assets altered.
