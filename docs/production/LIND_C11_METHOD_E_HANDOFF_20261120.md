# C11 Method E — individual polyhedral rock-mass sculpt (UNAPPROVED)

**Owner:** Claude.
**Where:** Draft PR #421, branch `feature/lind-cliff-rock-art-study-20261118`.
**Status:** candidate only. No adoption, canon change, main merge, deletion or publication.

## Why the method family changed

Independent G2 failed D4. The vertical grooves read as artificial, and the islands lacked rock-mass structure and hardness. The UV improvement was accepted and kept.

The cause was in D4's construction itself, so retuning D4 would not fix it:

- **Uniform columns.** Every cell was a uniform columnar Voronoi cell.
- **No real ridges or valleys.** Cell boundaries averaged the heights on either side.
- **One straight groove.** The fracture was a single long, straight riser line.

The director instructed a switch to per-block sculpting of the main masses and joints. D4 is preserved unchanged and used as the input.

## Inputs (SHA-pinned, unmodified)

| Input | SHA-256 |
|---|---|
| D4 `.blend` (CI artifact 14616152278, run 44708204132) | `0e560afc031f2356ade277e7b4f89eb01a2e62acdcda780c1c366112b90d99ff` |
| D4 carrier geometry | `ec2af2d59f922157de5a6f336c5c99208102e648a67b140a2f8eb994c42e0274` |
| Method C `.blend` (artifact 14606190629; identifies the repair faces) | `d0e91ae7543f2995b70c2a3f2d59e625d7cc828e6328ccc90c9224d060b0b545` |

## Method E

Script: `tools/production_qa/lind_blueprint/c11_method_e_block_sculpt.py`. It imports D4's helpers and UV method only; the D4 script itself is unchanged.

**Block layout.** Each island's footprint is split into irregular rock blocks by a power diagram with variable spacing (0.45–0.9) and weights.
- West: 28 blocks, footprint area 0.26–1.54, 4- to 7-sided.
- Central: 21 blocks, 5- to 8-sided.
- The main fracture follows the measured rail. It is built from staggered seed pairs, so it becomes a zig-zag of short, non-collinear block joints with varying depth.

**Each block is the minimum of its own planes:**
- **Front plane:** least-squares fit to the mass form over the block's footprint, then given an asymmetric tilt of 5–13°. It may stand at most 0.12 above and 0.20 below the mass form, so there are no spikes.
- **Fracture fold plane** (about half of the blocks): a convex break of 8–18°.
- **Side planes:** one steep plane per joint edge (38–64°, different on each side), starting below the block's own front plane. Neighbouring blocks therefore meet at offset, asymmetric joints.
- **Corner chips:** planes that break some corners.

**Surface.** The surface is `max(blocks, joint floor)`. Ridges and valleys are therefore exact plane–plane intersections:
- They are extracted from a 0.008-resolution label map.
- Crossings are solved analytically on each plane pair.
- They are simplified with Douglas–Peucker and inserted as constrained edges.
- Result: creases are crisp and follow the mesh edges. Creases of 12° or more are marked sharp.

**Perimeter.** A 0.12 blend band joins the blocks to the locked perimeter.

**UV and normals.** Same as D4: exact-boundary 3D mean-value harmonic map with untangling. Old loop normals are preserved (maximum drift 0.0198°).

Self-QA tuning before QA, all within Method E and recorded here:
- **E1:** blocks too small; read as a shard band.
- **E2:** pyramid apexes on the convex west flank.
- **E3:** a spike up to +0.55.
- **E4:** the current result.

E4 relief against the D4 surface: +0.26 / −0.24 BU at most; p1/p99 −0.15 / +0.20.

## Results (local Blender 5.3.0; two runs give identical geometry SHA and UV audit)

| | D4 | **E** |
|---|---|---|
| Carrier vertices / faces | 38830 / 40634 | 39468 / 41910 |
| Boundary / non-manifold / degenerate | 0 / 0 / 0 | 0 / 0 / 0 |
| Self-contacts | 0 | 0 |
| Protected vertices changed | 0 | 0 |
| UV flipped triangles / overlaps (repair, ring) | 0 / 0, 0 | **0 / 0, 0** |
| UV mismatch at the perimeter | 0 | **0** |
| UV anisotropy, median / p95 (ring: 6.97 / 27.2) | 11.43 / 20.1 | **9.39 / 17.5** |
| Longest straight crease run (west / central) | ~4 BU riser | **0.75 / 0.60** |
| Crease dihedral, median / p90 (west) | — | 29.9° / 70.9° |

- E carrier geometry SHA-256: `e226cb7a007a33da76541298af582a996ed12bbba84534a79a8f094397f893c3`.
- Local `.blend` SHA: `7d4c4067…`. This container hash depends on the output path, so compare the geometry SHA.
- Evidence is in `assets/candidates/lind/windwaiting-cliff-c11/method-e/` (with `SHA256SUMS`):
  - `review/`: fixed-camera PBR 3-view.
  - `clay/`: clay 3-view, close-ups and UV checker.
  - `compare/`: D4-vs-E PBR, clay and UV comparisons, island mask, XY sections.
- CI: `lind-cliff-c11-method-e.yml`.

## QA status

**G1: BLOCKED.**

**G2: NOT_RUN independently.** The author's own view, which is not a PASS:
- The straight groove and the columnar division are gone.
- The islands read as irregular polygonal masses with broken faces and asymmetric ridges.
- Risks to judge:
  - The west strip can read as stacked blocks against the softer inherited surroundings.
  - A few up-facing ledges pick up the turf colour, because the shader blends turf by normal direction.

**G3: PARTIAL_LOCAL.**

**G4: NOT_RUN.**

## Boundaries and next tasks

**Codex-owned region (C12: C8 fault panels, `shore_band`, staircase).** Not edited. Method E only edits faces that differ from Method C. The island perimeters are locked, and so are the old loop normals. Any Codex retopology must keep these island perimeters fixed, or rebase onto geometry `e226cb7a…`.

**Next:**
- **ChatGPT (non-author G2):** review `compare/D4_vs_E_pbr_front.jpg`, the low and oblique views, and the clay set, against the approved CG.
- **Codex:** run an independent UV/topology audit of the Method E CI artifact.

**Stop rules:**
- An input SHA mismatch or any failed check stops the run.
- A G2 FAIL for the same cause as D4 (straight or uniform grooves) cannot recur by construction; that is checked by `no_straight_crease_longer_than_0.9`.
- A second G2 FAIL on Method E's own cause (for example, "blocks read pasted") means changing structure. The candidate next structure: let the island perimeters move by an approved bounded amount, so the masses can continue into the inherited wall. That needs coordination with Codex ownership first.

## Attempt ledger (C11 repair-island defects)

- **B, C:** FAIL.
- **D1, D2, D3a:** self-QA FAIL.
- **D3b:** G2 FAIL and UV FAIL.
- **D4:** G2 FAIL (grooves artificial, mass and hardness lacking); UV result accepted.
- **E (this candidate):** new method family. E1–E3 are self-QA tuning steps, not separate QA attempts.
