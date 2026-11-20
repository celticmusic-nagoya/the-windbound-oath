# Morwen voxel head first real render — independent visual QA (2026-11-19)

**Source:** Actions https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44546941971, artifact `14540454690`, archive digest `sha256:e8d1cbcefa298e33cd2cada2d07c61e8c149424efb0faad02b2f08334a72880c`, expiry 2026-12-03. Blender `5.2.4 LTS`, saved candidate `MORWEN_VOXEL_HEAD_FIRST_SCULPT_CANDIDATE.blend` SHA256 `7263de6c02db07a5ea60e9769649372814493920028a190334c34afdd3e4cfc1`.

## Verified
- Saved .blend reopened in Blender Actions; actual Cycles CPU renders `front/right/back/left/three_quarter.png` downloaded and visually inspected, plus `QA.json`.
- One unified voxel-remeshed head mesh: **22,772 vertices / 22,770 polygons**, voxel size 0.009 provisional local units. No legacy face imported.
- This is a **rough massing study**. It does not establish professional anatomical sculpting or a finished head.

## Independent art QA — G2 FAIL
- Front: exaggerated bulging spherical cheek masses and a detached-looking horizontal nose tip; ocular anatomy is absent, forehead is smooth, chin is a separate rounded protrusion.
- Three-quarter: cheeks read as pasted hemispheres, nose bridge and tip do not form credible planes; no convincing orbital rim/eyelids.
- Side: nose projects as a short cylindrical appendage, jaw/chin proportions are unsuitable for approved character appearance.
- Back/left: insufficient fill lighting, silhouettes are visible but anatomy is hard to judge.
- Hair, eyes, glasses, ears, clothing and design-specific details **not present**; no comparison to official Layer 0 sheet was performed. Cannot claim official likeness.

## Gates
- G1 **NOT_RUN** for new geometry vs official reference.
- G2 **FAIL** for visual sculpt quality, independent image review.
- G3 **PARTIAL PASS** Blender reopen, mesh existence, 5 PNGs; UV, rig, facial topology, glTF, deform QA NOT_RUN.
- G4 **NOT_RUN**.

## Causal diagnosis / method switch
Voxel-remeshing disconnected generic spheres does fuse topology but does **not** solve art-directed facial plane construction. Repeating radius/voxel-size tuning is not a valid fix. **STOP this generic sphere massing family as production method** (one visual failure recorded, no reason to rerun). Preserve files as evidence; do not delete.

## Next production task
Obtain approved Layer 0 4-view visual landmarks; create genuinely hand-directed/brush-sculpted face anatomy or adopt an **unmodified, license-verified CC0 base** then sculpt according to design. Prioritize eye sockets, brow/orbit, nasal alar transitions, cheeks and chin in front/profile; avoid generic sphere assembly and old ring-based cage. Produce actual editable .blend, front/profile/3-quarter clay and design comparison, independently QA before hair or retopo. HairHarpy remains optional and uninstalled, not a blocker. Do not merge G2 FAIL candidate into main.
