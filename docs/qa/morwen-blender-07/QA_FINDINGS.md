# MORWEN-BLENDER-06 / 07 independent QA findings

Source: GitHub Actions 43223331789 (06) and 43223696561 (07). Extracted JSON from artifact 13945339531.

| View | Raw IoU | Registered IoU | Translation (px) |
|---|---:|---:|---|
| Front | 0.40388 | 0.41881 | (+40,+2) |
| Right | 0.34343 | 0.35794 | (+5,+1) |
| Back | 0.40254 | 0.42306 | (-38,0) |
| Left | 0.30436 | 0.35506 | (-14,0) |

All four registered comparisons improved, but none demonstrates approved likeness. Front candidate bbox x=0 and back candidate bbox x=384 indicate clipping at the image boundary, so registered IoU is not a reliable artistic grade. Candidate profile width is 112px versus 221px right / 218px left in full-costume reference. These are *clothed illustrations*, not anatomical ground truth.

07 continuous core: 168 vertices / 146 polygons, Blender build+reload QA PASS. It is a new overlapping torso+pelvis shell; original 16-piece body remains visible and unchanged. Full-body continuous mesh, visual match, and real-device QA remain NOT_RUN.

## Next gate
- Correct camera framing using shared mesh world bounds and margin without cropping.
- Remove overlapping torso surfaces in a derived candidate only while keeping arms and legs visible.
- Render all four facings of 07, then repeat numerical QA and independent visual review.
- Preserve source files, 17-bone contract, and reference SHA. No merge, adoption or publication.
