# AIDAN FACET V2 — independent visual QA, stop decision (2026-11-16)

## Actual evidence
- GitHub Actions run 43782248901: first attempt cancelled during Blender installation (not a geometry failure); rerun completed successfully.
- Artifact 14188409914; PNG `aidan_facet_v2.png`, 960×720, SHA-256 `e49605b04b4f81dea08b5cd0f297354ddbcdafef15316f8d8c9a383ae03afc67`.
- Six stone meshes: topology validation PASS, no boundary/nonmanifold edges; renderer Blender 4.0.2.
- Independent visual inspection: **G2 FAIL**. Silhouettes remain rectangular blocks, triangular facets merely subdivide broad flat front surfaces, gaps and floating courses are obvious, not convincing fitted hand-laid fieldstone.
- G1 BLOCKED; G3 PARTIAL PASS (clearance, intersections, self-intersections, actual game dimensions unverified); G4 NOT_RUN.

## Root cause
The construction begins with perturbed cube corners and inserts face-center points. Triangulation changes shading, not the macro outline. Fixed six-block grid and unverified joint fitting creates discontinuous masonry. More seeds, microfacets, bevels, roughness, PBR overlays or small coordinate changes cannot solve the structural silhouette/joint issue.

## Stop rule and production pivot
**Stop** both broad-plane ring v1 and faceted-cube v2 for final stone master creation. No more random-cube variants or repeated render attempts for this root cause.
Next authorized non-destructive stage: curate a small set of CC0 high-quality scanned/hand-sculpted irregular stones with explicit URL/license/hash and independently art-direct the silhouette. Build a separately editable *corner master* and physically fit mating faces with measurable joints before using Geometry Nodes for repetition/distribution. Texture only after macro silhouette and course-fitting art pass. If scan acquisition is blocked, create a human-art-directed master specification and mark BLOCKED rather than claiming production quality.
No original/canonical assets changed. No main merge or publication.
