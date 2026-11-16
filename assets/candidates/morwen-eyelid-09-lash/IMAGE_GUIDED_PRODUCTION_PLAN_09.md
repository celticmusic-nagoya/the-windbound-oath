# MORWEN-IMAGE-GUIDED-09 — approved non-destructive production direction

## Goal and scope
Use the **official approved Morwen four-direction character images** as visual references for a precise, game-ready Blender character. Claude can assist with deterministic scripts, UV layout, projection/baking and material authoring. **Image projection alone is not a substitute for geometry, topology, rigging, or art QA.**

This document is a **production plan**, not a new canonical design or a claim of visual equivalence. Existing approved assets remain untouched. Never use the old failed cage method again as a proposed fix.

## Canonical source gate (G1)
1. Locate the exact officially adopted front, back, left, and right images and their manifests/commit SHA; compare hashes and the project official design specification. Record authoritative status and any asymmetry, hairstyle, shoulder strap, book, emblem, flower, clothing, and accessories.
2. Do not choose a candidate image merely because it looks plausible. If any authoritative image or priority is unavailable, mark G1 **BLOCKED** and stop any canonical texture bake or adoption.
3. Save reference hashes, provenance and allowed-use license for external materials. Do not overwrite canonical PNGs or existing Blender files.

## Asset architecture
- **L0**: protected base body, face and original Shape Keys; stable mesh IDs and UV.
- **L1**: independently modeled hair masses, brows, lashes, upper/lower eyelids; lash roots tied to verified eyelid margin in a stable local surface frame.
- **L2**: modular garments, fabric thickness, straps, decorations and equipment with preserved asymmetry.
- **L3**: UV/PBR and controlled projection of **authorized official** front/side/back references, with manually corrected seams and view-dependent mismatches.
- Animation: facial blend shapes, blinking, deformation under movement, game camera sizes and device constraints.

## Current eyelid evidence / root cause
EYELID-09 has 18 candidate lash strips (216 vertices, 90 faces) built from nearest-cage points. BVH surface QA reported **59 right + 64 left** lash/cage triangle intersections and **0 eye intersections**. This is **G3 FAIL**, not an approved eyelash mesh. Root direction is currently hardcoded to world +Z, and root normal uses nearest triangle normal; these are technical scaffolds and do not establish the artist-approved lid margin/tangent, clearance or curvature.

The CI quality gate now correctly fails on recorded intersections (run 43731233347). Preserve the failing evidence and count this as the first evaluated strip-geometry attempt; do not reset failure count by renaming or changing a small offset.

## Next bounded work
1. Read the per-strip collision JSON; identify the intersecting strip IDs and source triangles. Inspect contact patterns and local frames, including upper-margin tangent, lid-facing normal, and outward direction relative to eyeball center.
2. Redesign root-frame construction with a continuous tangent derived from the verified upper-margin curve and a geometry-aware outward normal, **not** world-up; treat the anchor point as candidate-only.
3. Produce **one** revised isolated candidate and compare per-strip intersection counts against the baseline. If still failing, stop this method after the second valid attempt and change structural method.
4. Once real surface collision is clear, add alpha-aware visual/card overlap QA, blink-pose sweep and protected Face/Shape Key fingerprint regression. Then 5-view art renders and actual in-game size/performance QA.
5. Build UV/PBR material/projection workflow separately on verified official imagery, without allowing texture projection to mask geometry failures.

## QA gates
- G1: official image priority and exact hashes — **BLOCKED** pending full canonical cross-check.
- G2: five-view artist review and faithful character details — **NOT_RUN**.
- G3: existing lash strips — **FAIL** (123 cage intersections); synthetic generation and model read-only audit **PASS**.
- G4: game display, motion and Android — **NOT_RUN**.

No merge to main, publication, formal adoption, destructive deletion or replacement without explicit user approval.
