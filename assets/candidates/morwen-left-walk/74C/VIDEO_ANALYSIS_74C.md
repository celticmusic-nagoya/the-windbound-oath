# MORWEN-ASSET-74C: video analysis report

**Result: BLOCKED.** No reference video was analysed: none of the three videos could be watched or downloaded in this environment, so no frames, joint tracks or timings were extracted (no OpenCV or MediaPipe run). Nothing in 74C is claimed to come from these videos.

| # | Reference | What could be checked | Status |
|---|---|---|---|
| PRIMARY | "Walk Long Stride – Young Adult Female" (Endless Reference). The link is a YouTube **search URL**, not a video URL | The YouTube search page is blocked for automated fetching (robots). The video could not be identified, so its existence and licence are unconfirmed | BLOCKED |
| SECONDARY | https://vimeo.com/69217700 | Page metadata only: title "Animation Reference - Female Standard Walk - Grid Overlay", uploader AIE. Duration and licence not shown. The video itself was not playable or downloadable here | BLOCKED |
| TERTIARY | https://vimeo.com/1107097376 | Page metadata only: title "FEMALE WALK". The description says it is a 3D walk cycle made as class practice on a rig the uploader does not own. The page asked for a human verification step. The video was not viewed. The licence is not stated, and the rig belongs to a third party, so its suitability as a production reference is open | BLOCKED |

## Basis of the 74C motion design
- The key poses follow general walking mechanics: heel strike → loading → mid-stance → heel rise → toe-off → swing. Stance is about 60% of the cycle; the head stays steady; arms swing opposite to the legs.
- The design values are in `build_meta_74c.json` (`key_poses`, `stride_px_96`, `pelvis_rot_px`, …). They are design choices, **not measurements**.

## What is needed to run the analysis
- One of the following, placed in the repository or attached:
  - a video file (MP4 or MOV, side view, constant camera, at least 2 full cycles), or
  - a numbered frame sequence (PNG or JPG).
- Confirmation that the video may be used as a reference.
- With that, the planned extraction is:
  - foot contact and toe-off frames;
  - ankle, knee and hip trajectories (MediaPipe Pose);
  - pelvis and head vertical travel;
  - arm swing phase;
  - cycle time and stance/swing ratio.
- The results would then be re-applied to Morwen's 2.8-head proportions by replacing `KEYS` and the motion tables in `build_morwen74c.py`. Morwen's body shape itself is not changed.
