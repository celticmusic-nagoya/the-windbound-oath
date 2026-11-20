# C11 Method D — blade root cause and slit-to-channel rebuild (UNAPPROVED)

Owner of this stage: Claude (detailed region reconstruction), Draft PR #421, branch
`feature/lind-cliff-rock-art-study-20261118`. Candidate only: no formal adoption, canon
change, main merge, deletion or publication. Read latest main `AGENTS.md` and
`SESSION_CONTINUITY_INDEX.md` first.

## 1. Root cause of the "plate / blade" defect (measured)

| Stage (carrier `Cliff C8 B`) | SHA-256 (.blend) | Verts | Blades in carrier-only render |
|---|---|---|---|
| C10 `windwaiting_cliff_C10_UNAPPROVED` (art. 14580687938) | `8d0618dd…159223` | 37485 | **none** |
| junction_retopo (art. 14587169190) | `056ba4a3…5f2c` | 37720 | **both present** |
| bedrock_wall (art. 14590827331) | `a88fd515…d334` | 37720 | both |
| hero_fracture (art. 14591689110) | `0b6b0f3f…6508` | 37720 | both |
| C11 Method C (art. 14606190629) | `d0e91ae7…b0b545` | 37720 | both |

- The two blades appear at the **junction stage** (`sculpt_junction.py`), not in C11.
  Exactly **388 vertices** of junction_retopo have no coordinate match in C10; they form
  two clusters coinciding with the blades: west x −8.26…−7.41 (z 0.95–6.10) and central
  x −6.08…−5.41 (z 2.32–6.95). IDs persist unchanged through bedrock/hero/C11 C
  (`c11_boolean_slit_vertex_ids.json`).
- They are the EXACT-boolean V-notch cutters (`RAILS`): slits 0.18–0.72 wide but 0.30–0.87
  deep, 4-station ruled planar walls up to 2.4 tall, unbevelled lip. Depth maps / XZ
  sections (`rootcause/`) show narrow +0.5…0.75 grooves; under the review light the lit
  slit wall reads as a raised plate.
- Methods B/C displaced a *different* face island (x −5.95 ± 0.46 recess), so the slit
  geometry survived unchanged → both G2 FAIL for the same unaddressed cause. The nine
  suspect faces in `suspect_faces.png` were only the slit-intersecting sample.
- Separate pre-existing defect (not fixed here): voxel-staircase dark bands present
  already in C10 (visible in clay renders). Needs its own stage.

## 2. Method D (structurally different from B/C)

Script `tools/production_qa/lind_blueprint/c11_method_d_channel.py` (Blender 5.3.0, input
SHA-locked to Method C `d0e91ae7…`). Per fracture rail: select slit faces + topological
k-ring (west 2, central 1), split into connected components, delete each island while
keeping every perimeter vertex bit-for-bit, refill with a projected constrained-Delaunay
triangulation (first fold-free axis from a fixed azimuth/elevation grid; convex-disk
parameterisation fallback), solve a harmonic height membrane from the perimeter, then
carve an authored asymmetric fracture channel along +Y (width/depth > 1.5, rounded lip,
dipping bedding ledges, low-amplitude grain) faded to zero at the perimeter. Carve is
clearance-limited and contact-relaxed against untouched geometry. UVs fitted by
least squares from perimeter UVs (RMS 0.004 / 0.0002 / 0.010). No boolean, no extra sheet.

Attempt ledger (same defect "C11 blade"): B FAIL, C FAIL (Codex/ChatGPT record);
D1 geometric-tube + projected membrane → curtain over recess + serrated crest (self-QA
FAIL, not committed); D2 ring + poke/3D Laplacian → fan triangles, 125 contacts (FAIL,
not committed); **D3 = this candidate**. Do not rerun D1/D2 families.

## 3. Result (local, Blender 5.3.0 official build, SHA-verified)

- Candidate `c11_method_d_channel_UNAPPROVED.blend` SHA-256
  `61181a1fb2528bc54da3a2fd384e7086d460e41e8d71d8bd5c08e715f48942db`; carrier geometry
  SHA-256 `8b863289eb85b5b06fa21aa2f62c551cc068d180eb703a8262741909698a1103`.
  Two independent local runs byte-identical.
- Carrier 37720 → 39332 verts, 37783 → 41642 faces; 0 boundary / 0 non-manifold /
  0 degenerate; consistent winding; local self-contacts 0 → 0; all 388 slit vertices
  removed; all vertices outside rebuilt islands unchanged; source SHA intact.
- Fixed-camera review (unchanged `c11_render_review.py`, front/oblique/low):
  `review/`. Both blades are gone in all three views.

## 4. QA status

- G1: BLOCKED (no formal map-scale approval; unchanged).
- G2: **NOT_RUN independently.** Author self-review: blade defect resolved; remaining
  concerns — refill reads slightly soft/lumpy vs faceted surroundings (west), crest notch
  where the west slit crossed the lip, pre-existing C10 staircase bands. Not a PASS.
- G3: PARTIAL_LOCAL (carrier-local topology/contacts/winding/UV only). Whole-scene G3,
  LOD/UV texel density and custom-normal review NOT_RUN.
- G4: NOT_RUN.

## 5. Next executable tasks

1. **Codex (technical QA):** check workflow `lind-cliff-c11-method-d.yml` run on this
   commit; confirm `reproduces_claude_local_geometry`; run independent topology/contact/
   UV/normal audit on the Artifact `.blend`; do not edit Claude's script in parallel.
2. **ChatGPT (independent art QA, non-author):** compare `review/C11_methodC_vs_methodD_fixed_cameras.jpg`
   and the Artifact renders against the official CG (`assets/approved/game/cliff/sunset_background.png`);
   judge G2 for blade removal, fracture readability and silhouette.
3. If G2 FAILs on softness: next bounded geometry step is crisp joint facets inside the
   channel (planar jointing, not more noise) — owner Claude. Staircase bands from C10 are a
   separate stage requiring its own root-cause analysis.

Stopping conditions: input SHA mismatch, any failed check in the report, or a second
G2 FAIL for the same Method D cause → switch method family and record why.
