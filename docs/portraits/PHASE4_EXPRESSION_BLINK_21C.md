# DIRECTIVE-21C —15expression blinks, Android QA provisional

120PNG (15faces ×2eyes ×4stages), exact bytes from private handoff `handoff/phase4-21b-claude-20261030` @ `883624694e73a0839fc0db684ca76067765e7338`, `reports/PHASE4-21B-20261030/`. User explicitly authorized **PROVISIONAL_ANDROID_QA**, not formal adoption. [Per-file SHA/source/box ledger](PHASE4_EXPRESSION_BLINK_21C.json).

- Fiona/Lou/Emma: angry, sad, surprised, worried, determined.
- Static: Fiona smile/relieved, Emma smile/relieved (4faces).
- Lou smile/relieved remain unadopted/unregistered.
- The formal21A22expression PNGs and24normalblink PNGs remain unchanged. New overlays are in separate `provisional-21b/blink/` folders; normal paths/coordinates/timing/drawing remain unchanged.

## Source consistency and integration

Reviewed HANDOFF, source SHA list, all3comparison plates,15nine-frame GIF previews,120PNG SHA lists, boxes and source generation script. Source19expression +24normalblink hashes all match the authoritative21A adoption record even though Claude's handoff used the identical PR91 baseline. No handoff source is trusted over the formal lock.

Existing PortraitRegistry adds the five blink face IDs per character and selects a separate path for non-normal overlays. PortraitBlink/TalkPortrait shared control/drawing code is unchanged. DEV motion buttons/frame controls already discover capabilities through the registry. Existing production FieldTalk portrait face metadata automatically receives the corresponding blink; no committed dialogue/flags/progression/save/battle data changes are made.

The21A guard continues to pin every formal image byte and the actual formal expression/normalblink path set. Its old normal-only-motion assertion is superseded by this explicitly authorized motion extension; m50 separately verifies all15newmotionfaces, static4, source/current SHA and pixel behavior. Formal PNG lock/digest, adoption status and excluded-material protections are not relaxed.

## Intended material behavior and residual art concerns

- Already narrowed angry eyes may have almost unchanged s1/s2. Do not require five unique pixel images for every expression; verify actual closed pixels and exact restoration instead.
- Surprised has a larger first closing step; Android inspection pending.
- Lou right-eye tiny bright lower points are inherited from the formally adopted normal blink; Android inspection pending.
- Closed s4 matches the formal normal-closed eye within the normalblink area. Expression-specific pixels outside that area remain intact; it need not equal normal over the whole box or portrait.

## Android check

Game→DEV→立ち絵・モーションテスト→Fiona/Lou/Emma→one of the5faces→manual/auto/loop/frames. Check both sides/rotate, and compare surprised frame0→1 and Lou right lower lid. Smile/relieved for Fiona/Emma stay still. Existing DEV candidate labels are UI metadata; authoritative formal/base status remains21A, while these120overlays alone are provisional.

Physical Android final adoption: user pending. No automatic formal promotion.
