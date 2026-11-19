# MORWEN Layer 0 four-view source visual inspection — 2026-11-19

Status: PRODUCTION REFERENCE REVIEW ONLY; NOT FINAL ART QA OR ADOPTION.

## Byte-level evidence
- Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44504822756
- Artifact ID: 14519157153, ZIP digest: sha256:ca25ddcfc80a9bc88a3e932ebeefa5740c0b2f27baf4dd327267d259c68ac6e9
- Verified four PNGs (384×1024 each), exact SHA-256 per `docs/production/morwen_layer0_recovered_source_inventory_20261118.json` and Artifact `reference_verification.json`.
- Source: PR #419 `tools/blender/production_mesh_08/references/{7809,7807,7810,7808}.png`; image bytes verified against **reported reference hashes**, not the historical v5.61 JPEG hash.

## Direct visual inspection of contact sheet
- Front 7809: shoulder-length violet bob and bangs; symmetrical neutral stance; torso, limbs, stocking and lingerie-layer contours legible.
- Right 7807 and left 7808: opposite profiles with bob volume, chin/nose profile, bust, hip, knee and foot silhouette visible.
- Back 7810: rear bob taper, shoulder straps, back and leg silhouettes visible.
- These are **Layer 0 body/innerwear references**, not completed uniform, hat, glasses, book or accessory references. Do not derive missing equipment designs from them.
- The four images are visually coherent enough for *provisional body and hair volume study*. Perspective, exact world scale and unverified landmarks remain unresolved. Side views must not be assumed mathematically orthographic without calibration.

## Gate decisions
- Source integrity (SHA-256 and dimensions): PASS.
- Layer 0 visual usability for independent provisional body/head/hair blockout: PASS, **production reference only**.
- Full official design identity to historical v5.61 original: NOT VERIFIED; do not claim byte equivalence.
- G1 full character: PARTIAL / equipment-specific BLOCKED until approved references checked.
- G2 new authored sculpt: NOT_RUN; G3: NOT_RUN; G4: NOT_RUN.
- Provisional coordinates +Z up, -Y forward; no canonical dimensions assumed.
- Never import or repair old failed cage, ring-face or quad-patch geometry as new sculpt.
