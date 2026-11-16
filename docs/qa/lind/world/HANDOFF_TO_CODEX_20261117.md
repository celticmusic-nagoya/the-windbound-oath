# LIND-WORLD-01 → Codex WORLD/ROUTE handoff (2026-11-17)

Status: **Claude WORLD lane STOPPED by director instruction (2026-11-17).** No further new production on this branch. Candidate is preserved for Codex reference only; Codex candidate D (#346) / pipeline (#350/#351) remain the active WORLD/ROUTE line.

## What exists (candidate c01, interrupted mid-revision by an API rate limit 2026-11-16)
- Interface JSON `docs/production/lind/world/lind-world-terrain.v1.json` (PROPOSED_NOT_LOCKED).
- Scripts `tools/map_blender/lind/world/build_terrain.py`, `terrain_fields.py` (bpy 5.3.0, seed 20261116).
- `assets/candidates/LIND-WORLD-01/lind-world-terrain-c01/` .blend + 6 renders + build_manifest.json.
- Technical QA script was **not written**; attempt ledger **not written**.

## Known deltas recorded by the lane before stop (self-review, not independent)
- Village CGs show river/bridge ~50–70 m from the wind stone; c01 places them 130–230 m away.
- Raid riverside-cliff camera hides the river.
- Visible heightfield seam lines; materials flat; cliffs underscaled vs. approved master PNG.
- c01 was built before the master PNG (SHA abbb3997…0620, registered at dc17dd4) was available; it is **not** compared against it.

## Gates
G1: master PNG SHA verified by lead (PASS for source registration) — c01 image concordance **NOT_RUN**. G2 NOT_RUN. G3 NOT_RUN (no QA script). G4 NOT_RUN.

## Reuse guidance
Usable as reference: CG sightline notes in the interface JSON, river N→S and two-cliff separation constraints. Not usable as accepted geometry.
