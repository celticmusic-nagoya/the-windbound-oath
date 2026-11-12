# BLENDER-19 measured cross-section QA

**Technical QA PASS / Art QA NOT_RUN**

GitHub Actions: 43245124842 PASS. Regression BLENDER-01: 43245124239 PASS. Artifact: 13956063906.

Measured world-space sections from BLENDER-18 baseline:

| section | width X | depth Y | depth/width |
|---|---:|---:|---:|
| chest | 0.1235401 | 0.2061579 | 1.669 |
| waist | 0.0994321 | 0.1440000 | 1.448 |
| pelvis | 0.1052130 | 0.1600000 | 1.521 |

These values are **measurements, not artistic target dimensions**. Depth exceeds lateral width at all three sections; this merits checking against the official side silhouettes, not blindly scaling Y.

**Blocking next step:** trace the torso's outer front/back and side contours from the four SHA-locked canonical reference PNGs, taking care to distinguish clothing outline from body anatomy. Normalize orthographic camera and body height. Fit a stylized anatomy proxy and render flat unlit silhouette views. Do not declare artistic PASS or change the official model until independently reviewed. Draft only; no main merge or publication.
