# MORWEN-BLENDER-22 QA

**Technical QA PASS; artistic review NOT_RUN.** Run 43321151717 PASS, BLENDER-01 regression 43321151708 PASS. Artifact 13991106128 (`morwen-blender-22-review-overlays`) is present, size 1,851,119 bytes.

Four self-contained SVG overlays and a review manifest are generated from SHA-locked canonical four-view reference PNGs. Overlays mark central alpha spans and chest/waist/pelvis guide heights. These are **clothing-inclusive**, not verified nude anatomical contours.

Do not directly use central alpha spans as torso mesh dimensions. Next gate: inspect each SVG, distinguish arms, hair, sleeves and garments from torso, then define a stylized anatomy proxy and independent visual QA before changing production model. No main merge or publication.
