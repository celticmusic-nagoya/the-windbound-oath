# MORWEN-HD-WALK-01 | Director decisions v2 (2026-11-10)

Scope: **DEV-only HD walk**, no production switch and no main merge. Canonical pixel left SHA-256: `5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8`. Superseded 3V left MUST NEVER be loaded. All originals and existing derivatives remain byte-for-byte unchanged.

## Decisions

1. **Drawing anchor**: generate new WALK frame derivatives directly on **1200x1600 RGBA**, boots centered at **x=600** and ground y=1540. Do not also apply `anchor_dx` to these walk frames. Existing bbox-centered display derivatives keep their measured metadata corrections; do not overwrite them.
2. **In-game scale**: for the DEV HD mode, **hair-top to sole = 69 CSS px**, yielding approximately **76.5 CSS px including hat** at the measured v2 proportions. Evaluate headroom and collision separately; collision/interaction position is fixed to feet. Do not stretch to force hat into 69 px. 69 is a preview target; verify actual Aidan world units before runtime implementation.
3. **Occluded anatomy**: paint the far leg in all six frames and the far arm only in visible swing phases. Preserve direction of toes pointing toward screen left, cloth/stocking/boot design, proper fore/aft occlusion, and consistent anatomy; never use simple image mirroring as final art. New drawing is a DERIVATIVE, not an amendment to the master.
4. **Alpha**: keep source original alpha values (including 253). In each *walk output frame only*, quantize alpha to **0 or 255** after an explicit fringe inspection: meaningful silhouette pixels are opaque and the outside transparent; do not blindly turn every alpha>0 pixel opaque, which would retain halo noise. Derivatives must pass unique alpha set {0,255} and edge/no-halo QA.
5. **Head proportion / field policy**: maintain canonical approximately **7.5-head** silhouette in this separately named **HD cinematic/preview track**, not as the default production field sprite. Existing **2.8-3.0-head** default field rule remains in force. A future field-production adoption requires a separate director decision and consistency review across party members.

## Motion guidance
- Six unique left-facing frames, nominal 10fps; contact positions F1 and F4. Frame 1 and 4 must visibly differ by lead leg.
- Keep foot contact stable (no skating), test frame order and stride at both native resolution and 69px figure height; inspect 1x/2x upscale using nearest neighbor and game camera zoom.
- The recheck file's `stride_css_px=180`, `pelvis_bob_scaled_px=19.6`, `foot_span_scaled_px=735` are source-canvas planning values with ambiguous CSS naming: **do not interpret as actual screen CSS px**. Normalize through the chosen display scale and verify against motion references.
- Recheck for 1200px width clipping on both stride extremes, hat + cape + pouch overlap, grounded boot x=600/y=1540 on contact frames. Expand the WALK canvas symmetrically if needed rather than cropping or distorting, recording adjusted anchor coordinates. Existing display derivatives stay 1200x1600.

## QA gates
- Canonical asset SHA and frame source IDs; no superseded reference; no overwritten files.
- Frame dimensions, alpha binary, grounded anchors; toe orientation; no clipping, jump, sliding, wrong draw order.
- In-game-size animation check at target height, at least 1 complete loop, plus DEV viewport checks (PC / 390px portrait / landscape) and reduced-motion behavior where applicable.
- Preexisting test FAILs segregated from new FAILs; attach evidence and counts. Independent QA and Android are NOT_RUN until separately evidenced.

## Integration
Generate walk frames + separate manifest/config + opt-in DEV preview only. Leave production sprites, battle, SAVE, website public carousel, and original assets unchanged. Preserve Draft PR #221 and website Draft PR #25; do not merge or deploy. The official website can later surface a walk demo behind an explicit preview switch after art QA, not before.
