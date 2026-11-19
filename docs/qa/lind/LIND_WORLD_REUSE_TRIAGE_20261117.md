# LIND WORLD existing terrain audit — 2026-11-17

**Scope:** Source-based audit of existing Codex WORLD Draft PR #346, commit `d94b43361f360cbdc448b0a3ffdb15d9dd23e02f`. No new Blender generation or new visual inspection performed in this task. Existing independent QA report was read in full. Do not infer finished art from workflow success.

## Existing artifacts to preserve
- PR #346, `feature/lind-spatial-codex-01`.
- `assets/candidates/lind-spatial-codex-01/world/candidate-d/world.blend`, reported SHA-256 `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`.
- `assets/candidates/lind-spatial-codex-01/world/candidate-d/overview.png` and candidate manifest.
- `docs/qa/lind/LIND_SPATIAL_CODEX_01.md` and `docs/qa/lind/spatial-codex-independent/report.md`.
- Original reference `assets/sources/lind-world-20261116/original.png` SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.

## Evidence / triage
- WORLD study: continuous terrain 58,081 vertices / 57,600 faces; 27 mesh objects, source packed. Prior independent QA reports reopened .blend and actual PNG, not just scripts.
- A/B: geological art failed twice, **STOP smooth-heightfield/striped-rock method family**.
- C: road-specific grade-constrained cut/fill repaired steep/submerged endpoints but independently sampled road burial; preserve failed evidence.
- D: independent BVH 1,557 center/edge samples, **0 buried**. Candidate grades below proposed 25°; max unsupported road/bridge gap **0.444855 candidate units**. Nominal +0.05 clearance not proven. No support/junction/interior/navmesh approval.
- G2 **FAIL**: periodic/smooth cliff geology, sawtooth grass/rock boundary, abrupt terrain cuts, absent convincing bridge abutments, harbor approach and world detail. These are real unresolved art issues, not render failures.
- Workflow for latest commit `43880624862` reports success; this does not alter G2 or G4.

## Reuse versus replace
| Element | Decision | Reason |
| --- | --- | --- |
| Source image, provenance, seven collections, semantic graph | REUSE AS REFERENCES | source-review QA and source hash evidence, but graph/metric remain proposals |
| D road grade and sampled BVH QA scripts | REUSE AS TEST HARNESS | strong regression evidence; no claim of fully supported road |
| D continuous terrain as final world | REJECT FOR ADOPTION | final G2 FAIL and full G3 incomplete |
| Smooth-heightfield/striped cliff shader | STOP METHOD | exhausted art method A/B |
| Existing bridge/stone/vegetation candidates | PRESERVE / DO NOT EDIT | other lane ownership and prior failures |
| D scene as spatial reference candidate | CONDITIONAL STUDY ONLY | approved metric, camera, footprint and canonical CG reconciliation outstanding |

## New work allocation
WORLD geometry (separate owner/branch): authored geological cross-section + joint-constrained cliff sculpt, independent erosion/rock breakup, continuous turf/rock transitions; explicit harbor support and road/bridge junction geometry. Do not simply tune noise amplitude or material bands. Produce three clay views and measured junction/support geometry before materials. Define stop hypothesis: cliff faces must show nonperiodic joint structure at final display size, road support and junction physically continuous, and source geography respected. If new geometry is not available, mark BLOCKED rather than render the failed D model again.

INTEGRATION (this branch): coordinate and camera decision table only, provenance, independent QA criteria. No terrain generation, no merge or source replacement. Codex Method C bridge remains a distinct BUILD lane.

## Gates
G1 source integrity subset PASS, full spatial/canon/metrics BLOCKED.
G2 existing WORLD candidate FAIL, new method NOT_RUN.
G3 D sampled road nonburial/grade PASS; full WORLD G3 FAIL/INCOMPLETE.
G4 NOT_RUN.

## Next evidence required
- Current official world/CG comparison and approved spatial/camera/scale decision.
- Independently reviewed **new-method** sculpted terrain render and reopenable blend.
- Junction/road-support BVH tests including interiors, collision/navmesh; performance and Android tests later.
