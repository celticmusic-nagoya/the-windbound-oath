# MAP-BLENDER-19 independent review — structural stop

Status: TECH PASS / ART FAIL / NOT CANON

Evidence: GitHub Actions #43251449477; map19_report.json confirms 9/9 synthetic rays blocked, closed mesh, and SHA hashes. Render visually inspected.

Findings:
- Ridge remains a giant artificial slab behind the village.
- Base terrain and river terminate in obvious rectangular boundaries.
- Homes, square, bridge and paths remain regular blockout forms.
- Closing the ridge side walls does not solve terrain integration.
- Real cliff cinematic camera and traversable route checks are NOT_VERIFIED.

Decision: Stop incremental ridge mesh fixes. Two adjacent iterations (MAP18/MAP19) preserved occlusion but did not resolve visual structure. Do not create MAP20 as another patch on the same terrain.

Alternative: rebuild a single unified heightfield for the whole village and surrounding landscape, with cut river channel and cliff shoreline, then place buildings and paths by sampled ground height. Keep MAP19 as occlusion reference only. Define actual event camera/frustum and navigation corridor before claiming cinematic pass. Compare new candidate against MAP19 in identical field camera. No main merge or runtime integration.

Acceptance gates: no floating rectangular base edges in camera; natural landform transition; 9/9 synthetic rays plus actual event camera occlusion; passable paths and bridge; readable Android 390px preview; canonical geography preserved.
