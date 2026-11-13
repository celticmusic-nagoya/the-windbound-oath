# MORWEN-MESH-QA-02 — Connected component diagnostics

Evidence: GitHub Actions run 43440755715 (SUCCESS), SHA 171cd2e552551115b9769e45faca4c4b85050fe2, artifact `morwen-vroid-cc0-head-review/MESH_TOPOLOGY_AUDIT.json`.

| Mesh | Components | Largest component vertices | Components <=4 vertices | Components <=10 vertices | Vertices in <=10-vertex components |
|---|---:|---:|---:|---:|---:|
| Body | 179 | 1160 | 41 | 54 | 235 |
| Face | 34 | 588 | 2 | 2 | 6 |
| Icosphere | 1 | 42 | 0 | 0 | 0 |

Notable bounds (Blender local coordinates, meters or other scene units not yet verified):
- Body 350-vertex left/right pair: X [-0.15238,-0.00710] / [0.00761,0.15289], Z [0.11977,0.83346].
- Body 279-vertex left/right pair: X [-0.52507,-0.07541] / [0.07592,0.52558], Z [1.22514,1.30713].
- Face main 588-vertex component: X [-0.09208,0.09259], Z [1.35439,1.58652].
- Icosphere 42 vertices: X [-0.95106,0.95106], Y [-1,1], Z [-1,1].

Interpretation: symmetry and spatial bounds suggest intended separated anatomy or accessories, but **semantic part identities are not verified**. Tiny components are **inspection candidates only**, not automatically defective. The Icosphere's origin/role remains unknown. Do not delete or merge any components on this evidence alone.

QA: G3 component extraction PASS. G1 source preservation unchanged. G2 art fidelity NOT APPROVED. G4 NOT RUN.

Next: add per-component material IDs and triangle counts, and render an indexed spatial diagnostic to identify which islands belong to visible anatomy. Then assess candidate reuse against canonical four-view reference images. No source edits or automatic deletion.
