# MORWEN recovered face part fingerprint comparison — 2026-11-19

Verified [Actions run 44521332029](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44521332029) SUCCESS. Artifact 14527299884, digest `sha256:a55579c7b8bffaa879d0e32cc9a9c33aa7d20e09debd38b439b74677969a1acc`.

Comparing the extracted `structure.json` region SHA-256 values from PR #316 and #318:

| Region | topology | vertex coordinates | UV |
|---|---|---|---|
| FaceEyelash | MATCH | MATCH | MATCH |
| FaceEyeline | MATCH | MATCH | MATCH |
| FaceBrow | MATCH | MATCH | MATCH |
| MORWEN_Eyes | MATCH | MATCH | MATCH |
| Face skin | DIFFERENT | DIFFERENT | DIFFERENT |

**Interpretation:** PR #318 changes the face skin/eyelid region while preserving the tested eye/lash/eyeline/brow geometry and UV exactly. This confirms stable recovery candidates, **not** isolated rig/shape-key behavior or artistic acceptance. Fingerprints are based on 8-decimal quantized coordinates and per-face indices; full byte identity of underlying Blender datablocks is not asserted.

## Next required work
1. Inspect shared vertices and face-boundary dependencies between material regions; avoid destructive separation until proven safe.
2. Compare shape-key coordinates for face eyelash/eyeline vertices across neutral/Blink/Joy, and check weights, textures, alpha and modifier links.
3. Render actual front/3/4/closed-eye views and independent G2 QA against canonical Layer 0 references.
4. Keep PR #318 lid deformation **G3 FAIL**; no rerun of stopped annulus or procedural lid families.

G1 partial; structure/fingerprint QA PASS; new sculpt G2 NOT_RUN; rig/animation G3 NOT_RUN (historical lid FAIL); G4 NOT_RUN. No paid APIs, new PR, main merge or formal acceptance.
