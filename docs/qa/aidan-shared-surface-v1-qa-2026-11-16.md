# Aidan shared-surface contact v1 — result and visual scope (2026-11-16)

Evidence: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43787644597
Artifact id 14190384935, `aidan-shared-surface-contact-v1`: three rendered PNGs and `shared_contact_audit.json`.

## G3 limited feasibility PASS
Blender 4.0.2 workflow succeeded. Three meshes have zero boundary and zero nonmanifold edges. Planar support of the upper bond is 1.3944 units² (0.6972 west + 0.6972 east), 100% of its bottom footprint; nominal z gap 0; lower plan overlap area 0. This is **planar geometric coverage**, not triangle-triangle collision or guaranteed physical contact of irregular displaced stone faces.

## Render inspection
Reviewed front, top, three-quarter PNGs. They show a clean two-course rectangular block arrangement without the earlier floating upper boulder or triangular through-gap. **Not an artistic success:** the model is intentionally simplified, exhibits very flat and mechanically geometric faces, and does not resemble a dressed medieval masonry L-corner. The broad black shading on left/top views is from lighting/ambient shadow and cannot alone be interpreted as a structural hole. No final stone relief, PBR, canonical architecture geometry or game-scale evaluation is present.

Status: G1 BLOCKED for exact adopted house scale; G2 NOT_RUN for finished art (technical placeholder only); G3 PASS for limited coplanar support and manifold checks, NOT_RUN for actual triangle-level contact and collision; G4 NOT_RUN.

## Next stage
Keep this successful contact topology as a **technical constraint**, not an asset. Design a genuine architectural L-corner joint footprint, create independent dressed stones whose *contact faces are preserved exactly* while **only exposed surfaces** receive CC0 scan-derived geometric detail. Add actual contact/collision QA and 48px render; then independent G2. Avoid treating repeated bevelled rectangular blocks as production-quality stone. Preserve current candidate and audit unchanged.
