# AIDAN QUOIN — independent visual QA (2026-11-16)

Source: GitHub Actions run 43781482098, artifact 14188303489, head d371ba05437eead5f200eaa8b6fee6ae3d10723d.
Image: quoin_broadplane_v1.png, SHA-256 4890eb7e0b1674be192e3c8615543c3bceea2071f80343befc3a537562b619cd; 960x720, Blender 4.0.2.

## Actual evidence and assessment
- G2 FAIL: angular, repetitive horizontal belt silhouette; near-identical stacked courses; large unbroken cuboid backing visibly dominates. Not convincing as hand-dressed natural masonry or final game art.
- G3 PARTIAL PASS: Blender completed and emitted PNG and manifest. Both quoin objects report 30 vertices, 26 faces, zero boundary/nonmanifold edges, one connected component and positive signed volume. No collision, clearance, self-intersection, UV, texture or game-size verification.
- G1 BLOCKED: official architectural reference and dimensions not matched.
- G4 NOT_RUN: no integration or Android QA.
- PBR ASSET_NOT_ACQUIRED: placeholder material only.
- Do not treat green CI as art approval. Do not merge, replace official images or build additional walls from this geometry.

## Root cause and decision
Current method moves the same few plan vertices across horizontal rings, which produces uniform circumferential bands instead of large nonperiodic fractured faces. The identical plan and height across courses amplifies repetition. A rectangular backing fixture was left visibly exposed.
This is a **structural method failure**, not a bevel/texture tuning issue. Count broad-plane ring method as 1 failed G2 attempt; earlier Boolean-chip method also failed separately. Do not spend another attempt on cosmetic parameter changes.

## Required next architecture
Use an irregular per-stone face graph / manually art-directed sculpt or licensed scan, with independent large facets and nonrepeating silhouette, while retaining separately verified mating surfaces and clearance. Hide comparison fixture or use physically plausible infill stones. Match camera/light against previous candidate, and inspect game-scale crop before art PASS. Preserve baseline generator and this evidence.
