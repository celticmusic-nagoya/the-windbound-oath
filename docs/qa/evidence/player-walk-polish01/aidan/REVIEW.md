# Aidan up/down — independent static cadence/pose audit

Head inspected: e63780543d7ba1719a39a2f68b9924dc6d5b3933. Read AGENTS.md. Read-only images, metadata, source and history; no browser or asset edits/generation.

Recommendation: trial **150 world/cycle** for straight up/down first, keeping left/right180. This is a provisional timing recommendation, not a visually validated adoption verdict.150 cuts the current overly short six-pose exposure from50ms to83ms and cycle rate from3.33 to2Hz while changing stride less aggressively than180. Compare180 as the alternative if matching the adopted side cadence is more important;120 is a useful milder control. Static pictures alone cannot establish the final perceived walking quality or groundedness.

At300world/s, six equally timed frames:

|cycle distance|full cycle|per frame|frame changes/s|two-step contacts/s|
|---:|---:|---:|---:|---:|
|90 current|.300s|.050s|20|6.67|
|120|.400s|.0667s|15|5|
|150 recommended trial|.500s|.0833s|12|4|
|180|.600s|.100s|10|3.33|

“Two-step contacts” assumes these six poses encode one left+right cycle; that intention is plausible but foot-contact phase is not rigorously annotated in the source. Larger distance cycles reduce pose/bob frequency without slowing actual world movement; they can increase perceived foot sliding. Timing refinement cannot promise a no-slip match.

## Existing pose validity and limits

Viewed aidan-audit/vertical-contact.png at full display size, including separate enlarged legs. Current up/down banks each contain six distinct images, numeric01→06; FieldWalkMotion.ally sorts numeric suffixes and phaseDistance divides distance evenly among all six. No repeated alpha/source mapping analogous to side05/06 derivation was established here. The pose bank is used directly, not a hidden4-frame loop.

All12 metadata entries share canvas2048x1280, anchor1024/1230 and scale.0625; visible heads and sole baseline remain registered. Feet and lower legs are present; no obvious internal straight toe guillotine like the repaired side set is visible. No evidence justifies changing crop/anchor or source art during a cadence-only task.

The front/down set has uneven sole presentation: down02 shows a broad lifted sole on the image-left foot, down03 immediately presents a dark underside on the image-right foot; down04/05 both emphasize a forward image-right boot before down06 changes side. The back/up set likewise has sharply different sole exposure in02/04 and a concealed trailing limb in several intervening poses. This is not sufficient static evidence to declare anatomical impossibility or to reorder frames, but it is a specific reason that uniformly slowing all six may reveal pose discontinuities rather than remove them. Cloak/arm shapes also vary unevenly between neighboring drawings. Timing cannot add missing in-between leg articulation, change which leg is in front, or correct painted occlusion. If these remain noticeable at150/180, report an art/sequence issue for Claude rather than masking it with runtime resets, duplicate frames or repainting approved originals.

History: b706afcf03325fdfd2d1d1380bcf501b074c903b introduced current straight frontal/back drawings and retained older3/4 drawings as dl/ul. The earlier9452eb6 installation used sword-equipped6-frame front/back art. This supports separate straight-direction assets; it does not establish a documented per-frame heel-strike/contact ordering.

## Verification needed for final gate

Use normal NEW GAME/keyboard travel in both vertical directions, not only DEV: observe all six actual decoded PNGs in order, full-cycle distance/time, unchanged world speed and side180, stop/turn/restart cleanup, and progress/SAVE invariants. Compare DEV at inherited candidate and rate1 using actual frame transitions. Visually watch02→03 and06→01 at normal field scale and enlarged preview. Preserve all original images and259 formal hashes. Physical Android and final exact-head independent QA have not been run for this investigation.
