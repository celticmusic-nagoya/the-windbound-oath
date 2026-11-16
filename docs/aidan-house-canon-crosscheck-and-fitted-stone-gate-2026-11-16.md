# Aidan house canon cross-check and next stone production gate — 2026-11-16

## Source verification
Read private canonical **main**:
- `celticmusic-nagoya/the-windbound-oath-handoff/reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md`
- `reference/lore/CANON_STATUS.md`
- Public game repository `main/AGENTS.md` and `main/docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`.

Canonical bible explicitly lists **Aidan's house** as a Rild village structure. Village is agricultural/pastoral and emphasizes lived-in details. The inspected bible did **not** specify numerical house dimensions, stone dimensions, stone layout, roof dimensions, or camera scale. Do not infer that these are officially locked. G1 is PARTIAL_PASS for village/world context and **BLOCKED for exact geometry/canonical architecture reference**. Seek the adopted architecture design master before final asset integration.

## Actual geometry and image evidence
- Source: Poly Haven `rock_moss_set_01_8k.blend`, CC0, SHA-256 `23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6`.
- Blender import: 6 real stone meshes, 63,127 tris. rock04 has 18 boundary edges / 27 non-manifold edges; exclude from first fitting tests.
- Isolated render: workflow https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43784760144 success, artifact `aidan-cc0-rock-silhouettes`; 3 angles each for rock03 and rock06.
- Visual review: rock03 flat/rounded slab, rock06 highly irregular with protruding spikes. **Neither directly acceptable as an architectural quoin**; no stone-to-stone fitting render yet.
- Tiny 48px thumbnails are preview comparisons, **not in-game Android QA**.

## Method switch and proposed next deliverable
Stopped failed family: procedurally distorted cubes / faceted cubes / horizontal ring blocks, G2 FAIL in multiple recorded attempts. New family: physically informed dressed-stone assembly using scan-derived irregular surface information and individually designed flat bearing/mating surfaces. Causal difference: *stone shape and fit are authored together*, rather than random cube perturbation followed by visual adjustment. Avoid treating rough photogrammetry rocks as ready-made dressed blocks.

**Next production unit:** one 2–3-stone corner course with independently editable masters, explicitly designed bearing/contact planes and variable joint thickness. Before building, obtain an adopted house reference/size or keep test unscaled and noncanonical. Validate in clay from three views and 48px reduction, then collision/clearance, and only then PBR/LOD. No approval based solely on topology/CI.

AI 2D-to-3D is optional for decorative elements and characters only when a verified approved input image and compute are available; no GPU inference has been executed. Do not replace Blender production with primitive Three.js approximations.

## QA
G1 PARTIAL_PASS (world) / BLOCKED (house dimensions); G2 NOT_RUN for new fitted corner assembly; G3 PARTIAL_PASS for source import and renders, NOT_RUN for fitting; G4 NOT_RUN. No main merge, canonical replacement, destructive deletion, or publication.
