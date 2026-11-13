# AIDAN-HOME-HYBRID-PRODUCTION-01

Status: APPROVED WORKFLOW DIRECTION / ASSET SELECTION PENDING G1–G4

## Production decision
Use the highest-quality legally reusable source for each component, rather than insisting on Blender Python procedural primitives. Blender remains an assembly/render/QA hub, not the exclusive authoring method.

## Source-of-truth hierarchy
1. Approved game design and existing canonical images/dimensions.
2. Verified licensed reference packages and provenance records.
3. Unapproved candidates and Pinterest visual references (never automatically promoted).

## Preferred component strategy
- Walls / stone corners / architectural shell: inspect the already hash-and-license-verified Kenney Fantasy Town 2 kit as a **modeling base**, but rebuild or replace visibly low-detail geometry as necessary.
- Roof: high-detail modular slate meshes (sculpted or custom meshes), non-uniform thickness and stagger, authored UVs; Geometry Nodes only for controlled placement.
- Wood frame / door / windows: independently modeled high-quality joinery and metalwork, optionally adapted from verified CC0 meshes.
- Stone, timber, earth: individual CC0 PBR candidates from Poly Haven or ambientCG, each requiring asset-specific evidence, hashes and visual tests before download/import.
- Props: source verified CC0 candidate meshes from Kenney/Quaternius or bespoke modeled details; keep original author/license manifest.
- Pinterest: shape and material reference only, not a source for extracting copyrighted model or textures.

## Intake gate for external assets
Record provider, canonical source URL, exact asset ID, author, license evidence, redistribution/derivative/commercial permissions, downloaded archive hash, mesh/texture file hashes, format, polygon count, texture resolution and dependencies. Keep candidate assets outside canonical paths. License strings alone are not proof of legal reuse.

## Modeling and integration
1. Establish a canonical-independent Aidan Home scale/anchor sheet from existing accepted designs.
2. Select a small set of vetted component candidates, not an indiscriminate asset dump.
3. Compare candidate components in 5 views at final game display size.
4. Remodel or sculpt only components whose silhouettes/materials fail G2.
5. Bake/atlas materials and optimize geometry for browser/Android.
6. Render deterministically in isolated Actions job; export SHA manifest, candidate renders and independent QA evidence.
7. G1/G2/G3/G4 are separate gates. Do not auto-approve from successful Actions.

## Initial prioritized candidates (not approvals)
- Kenney Fantasy Town 2: verified archive SHA and embedded CC0 License.txt are documented in aidan_external_asset_sources.json; assess the architectural base before reuse.
- Poly Haven / ambientCG: research candidate stone, oak and slate material IDs and verify each license.
- Quaternius: research props and joinery only after exact per-asset license verification.

## Cost / safety
No paid AI API calls. No secrets in workflows. No main merge, destructive asset replacement or publication. Use dedicated Draft PR and read-only Actions wherever possible.
