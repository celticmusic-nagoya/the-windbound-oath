# Morwen head study attempt ledger — 2026-11-17

Historical counters remain preserved in PR #339 and CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md. Annulus/zipper eyelid/mouth: two failures, STOPPED. Ellipsoid face/tubular hair: rejected, no retry here.

## Local runtime preflight
Cycles build lacks OpenImageDenoise. Initial render aborted before any PNG. Removed the optional denoiser dependency; CPU Cycles works. This is a runtime capability failure, not a new art-method attempt.

## Trial 01 — CC0 facial-topology fit + closed broad hair surfaces
Source stage SHA256 d47d140586ba27ca2bc83dabbe3620b39a4d3e91dae57a65874d42defc60836e. First executed art study of this method family. Ten PNGs, editable .blend and reopen evidence exist locally; Actions reproduction preserves the corresponding implementation.

Self visual QA FAIL: eyeballs project beyond supporting lids because their center is in front of the cavity; lip material selection paints neighboring skin; illumination clips pale highlights and loses the canonical deep-purple hair. Technical screening also detects uncapped glasses bridge/temples. Full-body views fit the frame; head close-ups deliberately crop shoulders, so whole-alpha framing is not the correct head-only test.

Causal correction: fit eye depth to actual source socket surface coordinates (front lids about Y=-0.133, cavity about -0.106), remove heuristic lip-face material mask, cap optical-frame mesh ends, calibrate neutral illumination and explicitly separate whole-body framing from close-up head framing. This is one diagnosed correction, not a reset of old counters. Nominal 7.75 is measured using source crown vertex 8063 and submental vertex 8064; independent anatomy confirmation remains pending.
