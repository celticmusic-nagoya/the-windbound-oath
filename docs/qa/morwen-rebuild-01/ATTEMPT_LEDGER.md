# REBUILD01 cumulative ledger continuation

This entry does not reset historical counters. Source histories remain pinned in PR419's production report to PR399/407/417. No finished Morwen art attempt has been added in this checkpoint.

| Root cause / method family | Cumulative history | Current action |
|---|---|---|
| Annulus/zipper eyes and mouth | 2 FAIL, STOP | Not rerun |
| Realistic coordinate fit + radial shell hair | 2 art FAIL, STOP | Not rerun |
| Broad central Grab | 2 undone distorted probes, STOP | Not rerun |
| Local Grab + low-density hair masses | 2 art FAIL, STOP | Not rerun |
| SC03 semantic eyelid corner quads | Initial local prototype, character G2 FAIL | Preserved; not used as the new body's source |
| Ellipsoid/tubes / arbitrary body loft | Rejected for finished art | Not used |

## RB01-REF-01 — reference registration, not an art model attempt

Input: four PNG hashes from the approved November 16 manifest. Exact byte verification and local Blender4.3.2 execution PASS. Added packed images, projection/camera tests and reopen tests. No mesh body added. Anatomical landmark fit and independent art QA NOT_RUN. This unlocks body source work, not final adoption.

## RB01-SOURCE-01 — different licensed source intake, not a fitted character

Input: official Blender Human Base Meshes 1.4.1, archive SHA811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515, decompressed .blend SHAe5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a.
Selected GEO-body_female_stylized (Julien Kaspar), rather than the failed realistic candidate. Causal difference is source topology/shape, with NO coordinate fitting or face repair. Its compatibility must be judged before spending sculpt time; source quality alone cannot establish Morwen identity. Control geometry: 12502 vertices / 12500 faces, signature606a5cbed38aa3318626a48185bde66d3ce9f9c1f39d2fe9b6e66783f9740c4c.

Local mirror HTTP403 was bypassed by neither credentials nor proxy changes; the authorized Actions execution acquired the official archive and verified both SHA values. Run44148074813 created the editable intake and six actual PNGs. Connector downloaded the resulting archive for review.

Technical issues detected after first source intake: incorrect normalized translation shifts the body in the render; apt chose Blender5.0.1, whose new header cannot reopen in local4.3.2. Neither is an art fitting attempt. Correct translation as (original_location - world_center)/height and assert all evaluated vertices lie within the frame. Pin CI to Python3.11+bpy4.3.0 for compatible editing. Preserve v01 artifact and local failed reopen log.

No head/face/hair/rig/costume was regenerated, and no claim of manual sculpting or retopology is made. Next: reviewed anatomical targets and actual full-body authored geometry; do not revive automatic facial fitting or primitive lofts to fit this new source. G2 independent review remains NOT_RUN.
