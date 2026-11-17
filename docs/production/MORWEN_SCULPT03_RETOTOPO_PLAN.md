# MORWEN-SCULPT03 | Face retopology and rooted hair production specification

Status: DESIGN_ONLY / UNAPPROVED. Source branch: feature/morwen-art-directed-sculpt-02 (Draft PR #407). Do not merge or replace canon.

Execution update: [partial eyelid topology checkpoint](MORWEN_SCULPT03_EXECUTION_CHECKPOINT.md) now contains actual new Blender quad geometry and renders. This plan's full face/hair deliverables and exit criteria are **not completed** by that local prototype.

## Source lock
- Input: assets/candidates/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend
- Expected SHA-256: 90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b
- Verify 5 packed reference images and their stored hashes before edit. The 3/4 illustration is aesthetic reference, not an orthographic measuring plate.
- Preserve hidden source meshes, candidate history, provenance and original assets. Stop as BLOCKED if any source hash fails.
- Check current main AGENTS.md and private canon before lore-dependent changes. No inferred canon.

## Root-cause hypothesis / method switch
SCULPT02 failed G2 because the underlying realistic facial surface topology and thick coarse hair volumes could not be repaired with local Grab strokes or crown-band corrections. Two unsuccessful revisions are recorded. SCULPT03 must not repeat that method family.

## Production method
1. In a separate collection, duplicate source face, mark protected landmarks and build a retopology surface using manually authored quad loops. Keep source face intact. Plan loop flow around both eyelids, mouth, nose alae and nasolabial transitions; avoid poles in deforming eyelids and mouth corners.
2. Establish a reference-registered orthographic front and side comparison at consistent camera and lens settings. Distinguish visible landmarks from inferred cranium. Establish eye opening, brow ridge, nose bridge/tip, philtrum, lips and chin as a coherent silhouette before sculpting detail.
3. Replace large single-mass hair patches with root-directed scalp sections: asymmetric fringe, temple transitions, continuous rear bob and overlapping secondary locks. Each lock must have root-to-tip surface flow, controlled thickness and nonuniform ends. Preserve the approved asymmetry and glasses clearance.
4. Preserve 7.749997-head body scale until independently reviewed; do not enforce this number by distorting the face. Glasses remain separate and must be checked for bridge/ear support.
5. Use actual editable Blender geometry. Scripts may automate validation, camera and export, but cannot count as completed manual art-directed retopology by merely reshaping primitives.
6. Save new candidate as morwen_sculpt03_v01_UNAPPROVED.blend, record source and output SHA, geometry delta and operation log. No overwrite of sculpt02.

## Review deliverables
- Editable .blend and source SHA manifest
- 6 fixed-angle color + 6 clay 768px PNG, plus 64px/128px sheets and side-by-side SCULPT02 comparisons
- Wireframe close-ups of eye loops, nose, mouth, scalp roots and lock overlaps
- QA JSON with G1-G4 statuses, independent art review and failure ledger

## Exit criteria
G1: 5 canonical image hashes match; registered front/side landmark deviations reviewed; no unapproved canon changes.
G2: Independent review accepts anime-styled face identity, almond-eye construction, asymmetric fringe and natural bob root/overlap. Otherwise FAIL.
G3: Source reopens; nondegenerate finite geometry, manifold/winding, intersection screening, UV/rigger readiness separately assessed. Screening PASS is not full G3.
G4: WebGL/Android in-game view and regression QA required before adoption; NOT_RUN until performed.

## Execution constraints
No paid services. No main merge, deletion, official asset replacement, or publication. If Blender execution or interactive geometry editing is unavailable, report BLOCKED_EXECUTION; do not mislabel a written plan or render-only workflow as new sculpting.
