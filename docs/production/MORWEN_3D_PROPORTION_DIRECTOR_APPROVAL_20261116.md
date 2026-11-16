# MORWEN-3D-PROPORTION — director decision

**Decision: APPROVED in chat on 2026-11-16.** The director explicitly approved reinterpretation of the approved character design at **7.5–8.0 heads** for the full-3D game.

## Binding production rules
- Preserve identity, facial features, purple bob haircut and bangs, round gold glasses, violet eyes, flower ornament, asymmetric witch hat, faceted hanging gem, academy crest, cape, shoulder strap, satchel, vials, pleated skirt, knee-high socks and boots according to the approved design sheet.
- Preserve anatomical **right-leg garter** and all left/right distinctions. No mirroring to create missing asymmetric details.
- Proportions: full height divided by chin-to-crown head height must be within **7.5–8.0**, excluding hat and shoes' heel extensions. This is the *approved 3D adaptation*, not a claim that the original stylized illustration has this ratio.
- Distinguish face/head identity from anatomy adjustment; do not stretch the original illustration or Layer0 textures into a final model.
- Original five images and manifest remain byte-for-byte unchanged. Their design authority is preserved; the director's ratio decision resolves the **specific stylized-illustration versus 3D-proportion conflict**.
- Separate mesh families: facial/head topology, sculpted hair locks, body/arms/hands, costume, asymmetric accessories, deforming rig and PBR materials. Generic primitives and the 7,872-vertex silhouette envelope are NOT production character meshes.
- Existing two failures of polar-annulus/zipper eyelid topology remain exhausted; no third attempt with same method.

## G1 scope and open issues
- **PASS_DIRECTOR_PROPORTION_DECISION**: the 7.5–8.0-head adaptation is authorized.
- **G1 full design conformance: BLOCKED** until an actual 3D model is independently compared to the approved 4-view source and accessory asymmetry is verified.
- **G2 NOT_RUN**, **G3 character mesh NOT_RUN**, **G4 NOT_RUN**.
- Source priority remains as stated in the five-image manifest; preserve earlier approved source as history, without deletion.

## Next production gate
1. Construct independently editable **character-specific** head and hair meshes, not an empty reference scene or bounding primitive.
2. Render front, back, anatomical left and right plus 3/4 face close-up, at close-up and actual gameplay size.
3. Verify head-height ratio from 3D geometry excluding headwear, SHA of source inputs, topology, facial identity and asymmetric attachments.
4. Record failure method family, reproducible Blender version, asset hashes, renders and independent artistic QA.
5. Keep all outputs candidates on the existing Draft PR branch. No main merge, replacement or publication.
