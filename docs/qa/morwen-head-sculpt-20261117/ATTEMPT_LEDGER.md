# Morwen head study attempt ledger — 2026-11-17

Historical counters remain preserved in PR #339 and CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md. Annulus/zipper eyelid/mouth: two failures, STOPPED. Ellipsoid face/tubular hair: rejected, no retry here.

## Local runtime preflight
Cycles build lacks OpenImageDenoise. Initial render aborted before any PNG. Removed the optional denoiser dependency; CPU Cycles works. This is a runtime capability failure, not a new art-method attempt.

## Trial 01 — CC0 facial-topology fit + closed broad hair surfaces
Source stage SHA256 d47d140586ba27ca2bc83dabbe3620b39a4d3e91dae57a65874d42defc60836e. First executed art study of this method family. Ten PNGs, editable .blend and reopen evidence exist locally; Actions reproduction preserves the corresponding implementation.

Self visual QA FAIL: eyeballs project beyond supporting lids because their center is in front of the cavity; lip material selection paints neighboring skin; illumination clips pale highlights and loses the canonical deep-purple hair. Technical screening also detects uncapped glasses bridge/temples. Full-body views fit the frame; head close-ups deliberately crop shoulders, so whole-alpha framing is not the correct head-only test.

Causal correction: fit eye depth to actual source socket surface coordinates (front lids about Y=-0.133, cavity about -0.106), remove heuristic lip-face material mask, cap optical-frame mesh ends, calibrate neutral illumination and explicitly separate whole-body framing from close-up head framing. This is one diagnosed correction, not a reset of old counters. Nominal 7.75 is measured using source crown vertex 8063 and submental vertex 8064; independent anatomy confirmation remains pending.

## Trial 02 — diagnosed correction, art remains FAIL
Eye penetration and broad lip miscolor improved; clip/coverage and actual projected head bounds pass. Face remains a generic realistic human rather than the canonical soft anime planes; fringe is a segmented helmet-like fan, locks lack art-directed flow. Self art FAIL (2/2 for coordinate-driven facial fitting + radial hair-patch assembly as a final-art method). STOP that final-art method family. Do not tune it for a third art attempt. Preserve the study as editable geometry and technical evidence only.

Next structurally different art method: interactively sculpt canonical facial planes on the licensed mesh with direct multi-view overlay review, then hand place/retopologize silhouette-led broad bob masses. This requires an actual sculpt/artist review pass; it is NOT implemented here. No credible unattended parameter adjustment demonstrated for the identity gap, so final art remains BLOCKED.

### Separate glasses technical defect and method switch
Trial 01 curve-to-mesh bridge/temples had open ends. Trial 02 enabled curve caps, but converted caps retained duplicate/disconnected endpoint vertices (48 nonmanifold edges per affected object). Curve-conversion closure method has failed twice: STOP. Switch to explicit indexed polygon-ring sweeps with shared endpoint indices and unique cap polygons. Hypothesis: all edges become manifold without changing the reviewed head/hair/face design. This is a technical topology correction, not a third art-fit attempt. Rerendering identical art to verify the structural correction does not reset either art or historical eyelid counters.
