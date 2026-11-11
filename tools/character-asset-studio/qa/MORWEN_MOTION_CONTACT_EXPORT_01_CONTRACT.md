# MORWEN-MOTION-CONTACT-EXPORT-01 — minimal implementation contract

Status: PROPOSED / NOT_RUN / no art adoption
Source evidence: PR #225, `qa/morwen-layer0-03-qa-02/REAL_MOTION_EVIDENCE.json`
Owner: Codex (implementation); ChatGPT (independent schema QA); Gemini (visual mapping); Claude only if rig semantics are ambiguous.

## Problem

The six-frame historical right-walk candidate exposes near/far local ankles and phase labels, not anatomical left/right sole contacts in world space. Never infer worldPx from sprite-local ankles or a static (600,1540) ground marker. Historical candidate is not the v1.0 rig.

## Export schema (one record per frame and anatomical foot)

```json
{
  "schema": "cas/real-motion-contact-export/1.0",
  "rigVersion": "1.0",
  "source": {"path": "EXACT_PATH", "sha256": "ACTUAL_SHA"},
  "coordinateSystem": {"units": "worldPx", "scale": "DOCUMENTED_SCALE", "origin": "DOCUMENTED_ORIGIN"},
  "frames": [
    {
      "id": "ACTUAL_FRAME_ID",
      "timeMs": 0,
      "actorTransform": {"translationPx": [0, 0], "rotationDeg": 0, "scale": 1},
      "feet": {
        "L": {"phase": "stance", "stanceId": "L-0", "contactPoint": "heel", "worldPx": null, "provenance": "ACTUAL_SOURCE"},
        "R": {"phase": "swing", "stanceId": null, "contactPoint": null, "worldPx": null, "provenance": "ACTUAL_SOURCE"}
      }
    }
  ]
}
```

The example is a shape template, not valid audited motion data. Nulls are placeholders and MUST block the final stance audit.

## Acceptance gates

1. Source SHA, frame count and timestamps match the actual generated sequence; distinguish candidate vs v1.0 rig.
2. Near/far-to-anatomical L/R mapping is explicitly grounded for each facing direction; otherwise BLOCKED.
3. Per-foot stance/swing and stance interval IDs are authored, not guessed from pixels.
4. Contact point semantics (heel, ball, toe) and world transforms are documented and applied consistently.
5. Only after all required values exist, convert to `cas/stance-frames/1.0`, run `audit_stance_contact.py`, and report per-foot drift and tolerance.
6. Never alter canonical PNGs, old manifests, or accepted proportions. Maximum two similar repair attempts.
7. Add fixture tests for missing mapping, null worldPx, missing transforms, and left/right inversion. Missing data must return BLOCKED/NOT_RUN, never PASS.

## Stop condition

If actual per-frame pose/actor transform data is absent, stop at a provenance-rich BLOCKED report and request a targeted generator export. Do not synthesize contact coordinates or promote v1.0 adoption.
