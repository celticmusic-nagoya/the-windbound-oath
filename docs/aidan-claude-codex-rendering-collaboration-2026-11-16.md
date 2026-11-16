# Aidan House — Claude / Codex / ChatGPT high-quality Blender collaboration (2026-11-16)

Status: **implementation handoff / routing instructions**, NOT evidence that Claude or Codex has executed. Work only in Draft PR #329 `feature/aidan-masonry-pbr-study-01`, derived from `feature/aidan-architecture-v3-01`. No main merge, official asset replacement, destructive cleanup or publication.

## Verified current baseline
- Source-of-truth policy: `main/AGENTS.md` and `main/docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`.
- Poly Haven `rock_moss_set_01` CC0 source SHA256 `23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6`.
- Scan-boulder clipping and independent silhouette ring methods both produced G2 failures: see `docs/qa/aidan-fitted-scan-corner-v1-art-fail-2026-11-16.md` and `docs/qa/aidan-joint-first-v1-independent-art-qa-2026-11-16.md`.
- Shared-surface planar bearing technical gate: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43787644597. 100% *nominal planar* upper support, no boundary/nonmanifold edges, no z gap. **Not a final masonry asset**, actual triangle collision and art not passed. See `docs/qa/aidan-shared-surface-v1-qa-2026-11-16.md`.
- Canonical house exact dimensions unresolved: G1 BLOCKED. All new studies are NONCANONICAL.

## Independent work allocation — do not overwrite another agent's work
### Claude — visual / Blender geometry track (isolated `feature/aidan-masonry-claude-art-01`)
1. Inspect existing master house assets and source/canon before changing geometry. Do not invent canonical dimensions.
2. Produce **one** professional-quality, hand-fitted, weathered medieval Celtic stone corner candidate using *shared exact mating surfaces*, with organic nonuniform exterior only. Do not use primitive-block dressing as final. The geometry must remain separately editable by stone, and preserve existing adopted asymmetric design.
3. Derive exterior relief from pinned CC0 scan geometry/normal detail where technically appropriate; license/source provenance and SHA must be preserved. Never embed unidentified third-party assets.
4. Deliver Blender Python source, deterministic seed/config, .blend if feasible, three camera renders, a 48px display proof, triangle/manifold metrics, texture provenance, and art decisions. Use GitHub Actions Blender CPU. No formal adoption claim.
5. Do not change the Codex QA script; avoid changes to existing canonical files.

### Codex — independent geometry/CI QA track (isolated `feature/aidan-masonry-codex-qa-01`)
1. Review `tools/map_blender/aidan_shared_surface_contact_v1.py` and its workflow for test validity and blind spots.
2. Implement a **separate** Blender 4.0 compatible deterministic QA tool measuring real mesh-level contact/penetration, not AABB or only XY rectangle overlap. Include watertightness, normals, scale, expected support and contact-area tolerances. Prefer BVH / explicit face triangles with robust coplanar cases; document limitations.
3. Verify actual output at final in-game pixel size (48px) and render path / artifact integrity. Tests should FAIL on earlier known broken v1 candidates, PASS only on evidence-backed conditions; do not fabricate a pass.
4. Save a machine-readable report and tests in separate files. Keep the formal art verdict independent of technical pass.

### ChatGPT — coordination / art acceptance
1. Compare outputs with the approved Aidan house reference; if exact official house dimensions/design inaccessible, G1 remains BLOCKED.
2. Review three-view images at native and 48px and assess irregularity, scale, joint seams, hand-laid masonry silhouette, material consistency and no detached/floating rocks.
3. Merge neither work branch nor PR into main without explicit director approval. Integrate only compatible non-destructive changes in the study PR after cross-QA.
4. Distinguish G1/G2/G3/G4 and preserve negative evidence. A successful workflow never substitutes for G2/G4.

## Tool / permission boundary
GitHub PR comments and this document **do not invoke** Claude or Codex. Invocation requires the relevant agent integration or user launching the agent against the task/branch. Do not claim delegated execution or model-produced assets without actual run/commit evidence. Avoid paid API keys, unapproved service connection, GPU quotas, and non-commercial AI outputs.

## Acceptance gates
G1 exact house canon + existing art integrity: BLOCKED pending verified source.
G2 independent art and 48px proof: NOT_RUN for future candidate.
G3 watertight, actual contact, collisions, Blender renders, manifest/asset hashes: NOT_RUN for future candidate.
G4 game performance, runtime view, Android: NOT_RUN.
