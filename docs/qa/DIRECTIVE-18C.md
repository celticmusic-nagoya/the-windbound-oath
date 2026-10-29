# DIRECTIVE-18C diagnostic

Baseline: `e1b49e334e959bb1c4395683b4aa81953ed07291` (immutable git archive).

Result: no reproducible blink rendering defect in Chromium, visible page, `prefers-reduced-motion: no-preference`, 390×844. The real production cliff bench interaction, without injected conversation tables, showed three natural blinks each on the existing smile and normal Aidan pages. Actual canvas pixels in both eye ROIs changed through open → partial → closed → partial → open, matching adopted source composites exactly in RGB. Twenty unique face/state/eye ROI checks have zero pixel difference. Natural captured frames and enlarged eye strips show complete eye closure.

All 54 adopted PNG hashes match SHA256SUMS. All 48 overlay PNGs return HTTP 200, byte-identical to source, with registry dimensions L84×52 and R44×36 at source x570,y268 and x672,y314. The two natural expressions requested 16 overlay images without failures. Under reduced-motion: reduce, the same real conversation stays open-eyed with no canvas changes for 6.5 seconds; this is intentional existing behavior.

Evidence: results.json, diagnostic.log, diagnose.py, *-actual-state*.png, *-actual-open-to-closed.png, *-actual-blink.gif and .mp4. The short clips are reconstructed from actual natural rendered canvas samples; they are diagnostic eye crops, not full-screen session recordings. Source full-frame PNG comparison outside the eye regions can differ in transparent RGB from browser premultiplication; the reported exact comparisons concern the opaque eye ROIs.

No production files or assets were edited. Android physical behavior remains unverified. A user report of no blink can be caused by reduced-motion preference or a hidden/background document; it was not reproducible under the stated ordinary browser settings.

## Saved evidence

Eye strips show actual production canvas samples in order: open, stage1, stage2, stage3, closed.

- [smile left eye](evidence/directive-18c/smile-L-actual-open-to-closed.png), [right eye](evidence/directive-18c/smile-R-actual-open-to-closed.png)
- [normal left eye](evidence/directive-18c/normal-L-actual-open-to-closed.png), [right eye](evidence/directive-18c/normal-R-actual-open-to-closed.png)
- Reconstructed actual natural blink eye clips: [smile](evidence/directive-18c/smile-actual-blink.mp4), [normal](evidence/directive-18c/normal-actual-blink.mp4). These are not full-screen session recordings.
- [Numeric diagnostic results](evidence/directive-18c/results.json)

`tests/moss/m44_aidan_story_portrait.py` now verifies three natural cycles per expression by comparing actual canvas eye pixels with the adopted PNG composites. The user's physical-device cause is not established; reduced-motion is a verified intentional suppression condition, not a confirmed diagnosis of that device.
