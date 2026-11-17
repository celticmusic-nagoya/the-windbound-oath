# SCULPT03 cumulative method ledger

This file adds evidence; it does not reset any earlier counter. Source SCULPT02
SHA-256: `90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b`.

## Preserved history

- [PR399 ledger](../morwen-head-sculpt-20261117/ATTEMPT_LEDGER.md): coordinate-driven facial fitting + radial hair assembly, 2 art FAIL, STOP. Annulus/zipper eyelid-mouth family, 2 FAIL, STOP. Ellipsoid/tubular family rejected.
- [SCULPT02 ledger](../morwen-sculpt02/ATTEMPT_LEDGER_02.md): broad central Grab, 2 ineffective undone probes, STOP; small local Grab plus low-density hair masses, 2 rendered art FAIL, STOP. Crown-band variants are not a new family.
- SCULPT03 workspace-only CI run `44112673006` succeeded. It created an unedited duplicate, not retopology; it is not an art attempt or an art PASS.

## SC03-EYE-CORNER-01 — executed local topology study

- Defect: inherited small realistic eye apertures; previous polar/zipper construction could fold and invert local flow.
- Method: explicitly authored corresponding upper/lower semantic stations, shared medial/lateral corners, lid rim/support/socket bands. No angular/polar parametrization, zipper triangulation, automatic face fit or source Grab strokes. Source body and all hair remain unchanged. This is a local mesh prototype, not a third full-character art-fit or coarse-hair trial.
- Hypothesis: authored correspondence can produce 32 connected quads per eye without corner duplication or deformation-induced zero-area faces/front-normal reversal at blink samples 0, 0.5 and 1.
- Execution: Blender 4.3.2, Python-authored mesh coordinates/connectivity. **No manual GUI sculpting is claimed.** 96 new control vertices, 64 quads, editable diagnostic shape keys. Two open boundary loops per eye are intentional and must be integrated into facial skin later.
- Evidence: [build manifest](build_manifest.json), [local technical screen](local_technical_screen.json), [local diagnostic sheet](local_topology_and_blink_sheet.png), [context renders](color_context_sheet.png).
- Measured: 0 loose vertices, 0 unexpected nonmanifold edges, 0 degenerate evaluated faces, 0 reversed front normals across the three samples. This narrow hypothesis passed; collision, eyeball clearance and real closed-lid contact are **not** certified by those measurements.
- Self art result: **FAIL for integration/readiness**. The enlarged local socket remains an overlay on the inherited face; inherited eye geometry is too small. Existing realistic nose/jaw and helmet-like hair remain. Do not tune these detached overlays into an alleged finished face. First executed prototype in this distinct family; no historical counters reset.
- Full gates: G1 BLOCKED (registration unaccepted); G2 FAIL (character); G3 INCOMPLETE (limited local screening only); G4 NOT_RUN.
- Next causal work: connect the new socket boundary into a genuinely redesigned facial surface with registered orbital/cheek/nasal flow and correctly sized/depth-tested eye geometry. Maintain independent front/profile decisions and source history. Hair root/lock redesign follows coherent face registration; no further coarse-cap or local Grab retry is authorized by this checkpoint.
