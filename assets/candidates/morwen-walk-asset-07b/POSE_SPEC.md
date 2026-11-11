# MORWEN-WALK-ASSET-07B — proposed left/right six-frame production brief

Status: **PRODUCTION PREPARATION / UNAPPROVED**. Use the four exact SHA-pinned HD v2 pixel originals explicitly requested for this task, archived without re-encoding in REFERENCE_PACKAGE.zip. This package does not replace the repository's global canonical manifests. No rejected candidate is an official frame.

## Full-body / canvas / timing

- Target each unique full-body frame as 1200×1600 RGBA, common canvas scale and head/body ratio. Do not normalize directions independently to hide source stature differences. If stride/hat/cape clips, propose a symmetric canvas expansion and update the target anchor; do not silently crop or stretch.
- Target anchor (600,1540) is a **drawing target**, not measured sole contact. Actual frame anchors/world contacts remain null until measured.
- Six frames at 10fps: planned t=0,100,200,300,400,500 ms; loop 600 ms. Left nominal timing is grounded in HD DEV guidance; right timing is a task proposal. Neither is a captured motion timestamp.
- Draw anatomical L/R feet explicitly. Facing direction and near/far do not establish anatomical identity by themselves. No contact-coordinate inference from the fixed canvas marker.

| Slot | Proposed pose, both independently drawn directions |
|---|---|
| F01 | Anatomical L leads at heel contact, R trails with toe contact |
| F02 | L accepts weight / foot-flat, R early swing |
| F03 | L mid-stance, R passing with knee flexion |
| F04 | R leads at heel contact, L trails with toe contact |
| F05 | R accepts weight / foot-flat, L early swing |
| F06 | R mid-stance, L passing with knee flexion |

These assignments are proposed authored pose instructions, not observations of an existing image. The manifest's measured `anatomicalFoot`, `contactPhase`, `stanceId`, `anchor` and `worldPx` therefore remain null. `pose.status` and `timeStatus` distinguish planning from evidence. Actual `timeMs` is null; the schedule is recorded separately as `targetTimeMs`. `imagePath`/`imageSHA256` stay null until a frame passes QA. `targetImagePath` is only a reserved destination.

## Immutable visual details (Codex source inspection)

- Purple blunt bob, gold-rimmed glasses, violet eyes; preserve visible ear flower/jewel as rendered in each side reference.
- Large purple hat, gold trim/patterns, drooping crown and pendant. Left/right head ornament visibility differs. The right reference includes the large flower, ribbon tails and leaf motif; do not mirror it into the left profile.
- Match the purple/gold bodice, white collar/cuffs, purple bow, shoulder cape/book emblem, layered long flared robe and its intricate gold motif, skirt panels, opaque thigh-high stockings and buckled/laced heeled boots. Preserve reference proportions; no chibi conversion.
- Right side visibly has the leather bag and shoulder strap; left side has different occlusion and visible front bottles/chain. Do not transplant or mirror the bag/strap.
- The supplied left image visibly has a shoulder book emblem. Historical ART-74A removed an emblem from an earlier chibi candidate; do **not** apply that old deletion to the requested HD left source. Likewise retain the actual v2 skirt/hat details rather than silently repainting them to match a later prose rule. Any actual cross-view design conflict remains a review issue, not inferred repair authority.
- Hidden far leg/sleeve pose needs an artist's independent construction. Never mirror one boot to make a backward-facing foot or infer hidden anatomy from a cloth silhouette.

## ART-74 review and limits

Read `feature/morwen-asset-74a-left-walk` at `cd5525c2dc122ac0cc3a199db15c868d3dce5b44`: 74A README, 74F README/PHASE_REPORT/build metadata. 74A is a candidate assembled partly from mirrored 72 geometry with asymmetric equipment edits; its UNVERIFIED details are not measurements. 74F is a **12-frame, 840ms** refinement at 96×128/48×64, not this task's 6-frame HD sequence. Its qualitative staggered arm/cloth motion is useful, but its numeric displacement/palette/PNG source and mirrored step are not imported. Current six-frame 10fps guidance comes from `docs/design/morwen-hd-walk/MORWEN_HD_WALK_01_V2_DIRECTOR_DECISIONS.md` and the new task. Historical artwork is not a canonical reference.

## Production gates

1. Layered artist pass: freeze source hat/face/costume layers; construct independent L/R pose layers and far limbs. Review one silhouette/contact key before producing twelve full frames.
2. Complete sequence: opposite lead legs at F01/F04, no duplicate/reused stills, natural loop and measured proportions; independent right-side artwork. Do not promote a static crop, rescale, or mirror to a walk frame.
3. New derivatives only: binary alpha {0,255} after explicit edge inspection, transparent exterior/leg gaps, no baked checkerboard/background, no clipped extremities. Original source translucency and bytes remain unchanged.
4. Measure native-canvas anchors and heel/ball/toe contacts per anatomical foot. Record real producer root transform/projection and source SHA; world contacts remain null until evidenced. Source05/Export04 input contracts require these, not just a drawing anchor.
5. Native and 69px figure-height loop QA, independent design/asymmetry QA, director adoption and Android hardware are separate gates. No automatic formal adoption, game integration or publication.

## Alternatives after capped generation failure

- Artist/manual retouch: protect source layers and redraw only pose-dependent legs/cloth using per-frame masks, followed by pixel-level design review.
- Rigged 2D production: create verified split parts and anatomical rig from the approved source, author a six-frame gait with actual pose/root data, then render each direction independently and export measured contacts.

Both require new evidence; neither treats the rejected model output as an adopted source.
