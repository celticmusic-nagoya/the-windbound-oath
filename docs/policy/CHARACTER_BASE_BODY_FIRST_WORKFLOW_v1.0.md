# Character Base-Body-First Workflow v1.0

Status: Director-approved policy (2026-11-11)
Scope: THE WINDBOUND OATH, all character multi-angle assets.

## Gate 1: Establish and freeze the base body
Before drawing costume or accessories, establish an unclothed/non-detailed anatomical construction model for front, back, right and left. Fix consistent stature, head-to-body ratio, shoulder and pelvis width, hip level, limb lengths, joint positions, feet and ground anchors. Use neutral, non-explicit construction shapes. Record landmark coordinates and measurements in a BASE_BODY_SPEC, and create a cross-view comparison. Do not proceed unless measurements and anatomical connections pass QA. Any pose-dependent silhouette difference must be documented separately from anatomical dimensions.

## Gate 2: Layer costume without altering the frozen body
Layer garments and props over the approved body: inner outfit, skirt, socks, boots, robe, cape, hat, bag, belts and ornaments. Do not stretch or relocate anatomical landmarks to fit garments. Changes to the body require explicit versioning and reapproval of Gate 1.

## Gate 3: Cross-angle structural consistency
Verify the robe is open in front, has a central rear slit exposing the skirt and leg silhouette, and has long, dramatically flared side hems near heel height. No long central fabric panel should cover the legs. The pleated skirt has a predominantly plain base and asymmetric check pattern only on the character's right side; check placement from each camera angle, never mirror it automatically. Preserve the approved front/back garter ornament configuration, side-specific bag placement and straps, hat flower orientation, and correct occlusion between arms, sleeves and robe.

## Non-negotiable visual invariants
Purple bob haircut, established face and glasses, green leaves beneath the hat flower, gold laurel motif on hat brim/band, purple/gold costume and high-definition illustration quality. No checkerboard background baked into images. Delivery PNG backgrounds must have genuine alpha=0 outside the subject, verified programmatically.

## QA and delivery gates
Each phase requires a dated QA report with PASS/FAIL/BLOCKED/NOT_RUN, side-by-side overlays and landmarks. A machine PASS alone cannot substitute for visual independent QA. Preserve original SHA-256 and separate official assets from candidates. Register source, layered candidates, measurements, MANIFEST with hashes, QA reports and comparison images in a GitHub work branch and Draft PR under AI_ARTIFACT_SHARING_POLICY_v1.0.md. Never silently overwrite official originals or merge/publish without director approval.

## Morwen transitional application
Apply this workflow to future Morwen revisions. Existing four-view real-art originals remain protected. For FIX-02, first reconstruct a common underlying body and document landmarks, then propose localized adjustments; do not falsely claim the existing fully clothed images were produced with a common frozen base. Keep Draft PR #221 pending independent QA and director adoption.
