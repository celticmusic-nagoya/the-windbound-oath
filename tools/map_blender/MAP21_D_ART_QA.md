# MAP21-D independent art QA — structural stop

Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43326742939
Source commit: 9e4c297af11483c413e51cc070e28b4646e44cfa
Evidence: rilde_map21d_field.png, rilde_map21d_cliff.png, map21d_report.json (SHA manifest).

Status: TECH PASS / ART FAIL / NOT CANON.

Visual findings:
- Beveled 3D curves create raised tubular roads, crossing terrain and each other. A path is not a traversable ground surface.
- River is still a blue surface ribbon, not a terrain-cut channel with banks.
- Sunset cliff camera points at a terrain boundary / empty background, not a valid sunset-sea composition.
- Building and bridge geometry remain greybox placeholders.
- Event occlusion and physical navigation remain NOT_VERIFIED; previous graph reachability is not a gameplay collision test.

Structural causes:
1. Path elevation was constant z=0.28 and ignored sampled terrain height.
2. Curve bevel_depth=.52 creates round pipes, not flat road ribbons.
3. Camera target is driven by schematic coordinates but lacks horizon/frustum QA.
4. Water has no corresponding terrain carving.

Stop rule: MAP21-B and MAP21-D both failed art structure. Do NOT add another superficial road/river overlay on the same model. Next candidate must use terrain-conforming flat road masks or decal ribbons with slope/width checks, a carved riverbed and water-level-aware banks, and an explicitly framed sea-facing event camera. Establish numeric QA and render comparison before asset decoration.

Acceptance: no floating paths, no jagged terrain roads, nonrectangular riverbanks, sunset camera includes sea/horizon, village fire not visible before return bend, 390px legibility. All acceptance gates require evidence; no main merge or canon adoption.
