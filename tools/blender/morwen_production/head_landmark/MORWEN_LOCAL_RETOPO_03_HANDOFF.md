# MORWEN-LOCAL-RETOPO-03 — production handoff (proposed; NOT executed)

## Preconditions and source authority
Read latest main and working-branch `AGENTS.md`, `docs/art/QUALITY_FIRST_3D_PIPELINE_V1.md`, `HEAD_STRUCTURE_01_AUDIT.md`, `HEAD_LANDMARK_02_REPORT.md`, `MORWEN_HEAD_TOPOLOGY_LAYER_ROADMAP_02.md`, and existing attempt ledger. Compare latest private lore canon/addenda/status and approved v5.61 art before claiming G1 complete. Preserve all source SHA values. The approved 3D target PNG (SHA-256 `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957`) defines **final artistic quality**, not just reference.

## Fixed facts
- Existing VRoid Face+Body is structurally complete; never extract the obsolete 588-vertex fragment.
- 3D baseline U (eye level to chin) = 91.5 mm. Front/right/left 2D U varies 1.65%. Calibrated side-profile nose protrusion deficit = 0.11–0.15U, but applying full 2D protrusion via RBF caused a spike (failed attempt MHL02-FIT-01, 1/2). Earlier jaw taper in PR #306 also failed G2 (1). Carry both counts forward.
- Reuse skull, neck and rig. Local retopology for nose/eyelids/mouth. Eyes, hair, glasses, hat are separate future geometry. Do not mirror canon asymmetry.

## Authorized next engineering task (non-destructive)
1. Create a dedicated branch from the reviewed #308 head. Do not modify or merge #308/#306 directly. Publish a Draft PR.
2. Build **one** local-retopology candidate for the nose bridge/tip and surrounding facial surface, using a controlled ring/grid with smooth curvature and continuous transitions, preserving untouched Face+Body, seam continuity, rig and expression compatibility. Do not use RBF handles on the nose. No simplistic primitive as final art.
3. Measure silhouette and surface curvature in front/right/left/three-quarter; generate shaded clay and wireframe close-ups with a fixed camera, plus matching 2D canon and 3D quality-target comparisons. Annotate landmark confidence and camera calibration. **Do not hardcode the 2D side-profile 0.49–0.53U nose protrusion as a 3D target.** Evaluate a small *design range* against the approved 3D target; record uncertainty and defer final aesthetic choice.
4. Validate normals, manifold/seam continuity, topology, neck boundary, UV/shape-key/weight implications and deformation under blink/smile. Explicitly mark unsupported expression-key transfers as BLOCKED, not PASS. Run deterministic local and Actions QA; include per-view artifacts and JSON metrics.
5. Use shared attempt ledger. On two failed attempts in one method family stop and switch to another topology technique; no micro-tweak loops. Never overwrite approved PNGs, main, or published assets.

## Decision boundaries
- Nose depth: art decision pending target-image 3/4 evaluation; do not invent approval.
- v5.61 binary: verify availability, do not fabricate or replace.
- Hair transparency/render engine and game-display polygon budget: pending; use opaque hair assumptions for *design only*, not finalized engine behavior.
- 1px eye-height difference: preserve source and label unresolved, do not enforce symmetry.
- G1 may only PASS for source preservation while full canon comparison remains BLOCKED. G2 candidate FAIL/NOT_RUN until independent art review; G3 only with evidence; G4 NOT_RUN until game QA.

## Deliverables
Candidate mesh/script, reproducible parameters, measured JSON, calibrated image comparisons, explicit deformation/regression checks, attempt-ledger entry, QA report, GitHub Actions link, Draft PR. Do not report completion before rendering and visual inspection.
