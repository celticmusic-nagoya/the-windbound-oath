# C11 Method D4: joint facets, continuous fracture and fold-free UV (UNAPPROVED)

This stage is owned by Claude (precision sculpt inside the Method D repair islands). It lives in Draft PR #421
on branch `feature/lind-cliff-rock-art-study-20261118`. It is a candidate only: there is no formal adoption,
canon change, main merge, deletion or publication. Read the latest main `AGENTS.md` and
`SESSION_CONTINUITY_INDEX.md` first.

## Inputs (SHA-pinned, unmodified)

| Input | SHA-256 |
|---|---|
| D3b candidate `.blend` (artifact 14613506757, run 44702017121) | `a6813fe0d65874b04c46106c49dfdbac67b980ff90e67128375ebcad911484ce` |
| D3b carrier geometry | `b3d289124c8a8fb724de4ca30d25e57ea1e7a90f620ccee2640c5c91a2a7c934` |
| Method C `.blend` (artifact 14606190629), the reference that identifies the repair faces | `d0e91ae7543f2995b70c2a3f2d59e625d7cc828e6328ccc90c9224d060b0b545` |
| Approved CG (rock language reference only) | `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07` |

## Defects addressed and their measured causes

1. **West soft/mottled relief (ChatGPT G2, comment 7034151523).** The D3 surface was a smooth harmonic
   membrane with a rounded channel profile, 2-octave noise and a ledge ripple, all smooth-shaded on a 0.055
   mesh. The neighbouring rock is faceted: dihedral p90 is 29–43° and edges are 0.11–0.14 long.
2. **Central fracture broken into dark cavities.** The central rail carve used `depth_scale` 0.5, and contact
   relaxation then halved the depth vertex by vertex. That fragmented the joint into pits. The island-mask
   render shows the remaining dark slots to the right of the central island lie **outside** it, in locked
   geometry. They belong to the C8 fault-panel family (Codex analysis, comment 7034493547), so they are owned
   by Codex and were not edited.
3. **Interrupted west crest.** The D3 taper left a notch where the channel met the crest. In D4 the joint ends
   below the lip.
4. **UV flips and overlaps (Codex QA).** D3/D3b mapped 3D to UV with a least-squares affine fit. That map
   folds wherever the surface turns against the fitted plane. Our audit reproduces Codex exactly on D3a:
   77 flipped triangles and 598 overlapping face pairs inside the repair, plus 719 overlaps against the
   neighbouring ring. D3b has 91 flipped triangles, 675 internal overlaps and 810 against the ring.

## Method D4

D4 is structurally different from D1, D2 and D3: there is no final membrane, no noise and no channel
profile. The script is `tools/production_qa/lind_blueprint/c11_method_d4_joint_facets.py`.

- **Re-tessellation.** The faces that differ from Method C are re-tessellated by constrained Delaunay
  triangulation. The constraints are an anisotropic columnar Voronoi joint network (0.20 × 0.55, after the
  vertical columnar jointing in the approved CG), the rail itself (bounded by mirrored seed pairs), and a
  riser-foot line.
- **Joint facets.** Each joint cell is one plane. The plane is fitted to the mass form (a harmonic
  interpolation of the locked perimeter plus an authored planar wedge) and tilted on a two-set asymmetric
  joint model: west +17°/−10°, central −15°/+11°. Each tilt is clamped to deviate at most 0.07 from the mass
  form.
- **Continuous fracture.** Rail-top heights are smoothed along the rail. The riser foot is set to the top
  height minus the depth `D(s)`, which tapers monotonically and has no noise, so the joint cannot fragment.
  The riser faces away from the review key light, so it reads as one continuous shadowed joint.
- **Edges and normals.** Creases of 20° or more are marked sharp; smaller creases stay smooth, giving
  restrained rounding. Loop normals of untouched faces are preserved (maximum drift 0.028°). Where a smooth
  fan crosses the perimeter, it inherits the old normal.
- **UV.**
  - The interior is an exact-boundary harmonic map with Floater mean-value weights taken from the 3D surface
    (all weights positive), followed by local untangling.
  - One perimeter "ear" had all three vertices locked and its old UVs locally reversed, so no interior
    placement could unfold it. Its interior edge was rotated, which is allowed only when the quad is convex
    in the domain.
  - Perimeter UVs equal the neighbours' UVs exactly, so the texture has no seam.

## Results (local Blender 5.3.0, deterministic over two runs)

| | D3b | **D4** |
|---|---|---|
| Carrier vertices / faces | 39721 / 42416 | 38830 / 40634 |
| Boundary / non-manifold / degenerate | 0 / 0 / 0 | 0 / 0 / 0 |
| Local self-contacts | 0 | 0 |
| Protected vertices changed | 0 | 0 |
| UV flipped triangles | 91 | **0** |
| UV overlaps inside the repair / against the ring | 675 / 810 | **0 / 0** |
| UV mismatch at the perimeter | (seam) | **0.0** |
| UV anisotropy, median / p95 (ring: 6.97 / 27.2) | 10.24 / 28.4 | 11.43 / **20.1** |
| Texel-scale ratio to ring, median (p5–p95) | 0.90 (0.51–1.36) | 0.84 (0.58–1.17) |
| Riser drop, minimum over 40 samples (west / central) | n/a (pits) | 0.196 / 0.140 BU |

- D4 carrier geometry SHA-256: `ec2af2d59f922157de5a6f336c5c99208102e648a67b140a2f8eb994c42e0274`. Compare
  this geometry SHA, not the `.blend` container SHA.
- Evidence is in `assets/candidates/lind/windwaiting-cliff-c11/method-d4/`, with `SHA256SUMS`:
  - the fixed-camera material 3-view under `review/`;
  - D3b-vs-D4 comparisons under `compare/`: material 3-view, clay 3-view, clay, material and UV-checker
    close-ups of both islands, an island mask and XY sections;
  - the full report and UV audits of D3a and D3b.
- Workflow `lind-cliff-c11-method-d4.yml` reproduces the run in CI and uploads the `.blend`.

## QA status

- **G1:** BLOCKED (unchanged).
- **G2:** NOT_RUN by an independent reviewer. Author self-view:
  - the west mottling is gone;
  - one clean continuous joint runs from below the crest to the foot;
  - the in-island cavities are gone;
  - joint facets read moderately. Many cells are tilt-clamped (mean tilt scale ≈ 0.53), so the angular
    jointing is subtler than in the CG.
  - This is not a PASS.
- **G3:** PARTIAL_LOCAL. Island topology, contacts, winding, normals and UV pass. Whole-scene G3 is not run.
- **G4:** NOT_RUN.

## Ownership boundaries and next tasks

- The C8 fault panels, `shore_band` and the staircase dark bands belong to **Codex**. D4 edits only the
  faces that differ from Method C, and every protected vertex and old loop normal is unchanged. The next
  Codex retopology must keep D4 island perimeters fixed, or it must rebase onto D4 geometry SHA `ec2af2d5…`.
- **Codex:** run an independent UV, topology and contact audit on the CI artifact. Do not edit the D4 script
  in parallel.
- **ChatGPT, as non-author reviewer:** judge G2 on `compare/D3b_vs_D4_mat_front.jpg` and the other
  comparisons against the approved CG.
- **Stop conditions:** an input SHA mismatch; any failed report check; a second G2 FAIL for the same D4
  cause, for example "facets too subtle" twice. In that case, switch structure, for example to a sculpted
  hero joint mesh, and record why.

## Attempt ledger (defects in the C11 repair islands)

- B, C: FAIL.
- D1, D2: FAIL (self-QA).
- D3a: self-QA FAIL.
- D3b: G2 FAIL (soft relief, pits, crest), UV FAIL (Codex).
- **D4 (this run):** a structurally new joint-facet and UV construction. Its self-QA iterations during
  development (metric fix, riser enforcement, UV ear rotation) are not separate method attempts.
