# FIELD-HD-7.5｜全体ビジュアル移行方針（2026-11-10 正式採用）

## Director decision
Human-proportioned HD field art targets **approximately 7.5 heads**, balancing cute, appealing facial design with elegant body proportions. This supersedes the previous 2.8–3.0-head baseline. The previous rule is not a production constraint for new human HD art.

## Design protections
- Official character portraits, silhouettes, hair, outfits, accessories, age and personality remain authoritative. Do not stretch existing chibi sprites to 7.5 heads or simply downsample realistic illustrations as final pixel art.
- Proportion is a **design target**, not a universal numeric mandate: adapt for children, elderly characters, dwarves, fairies, monsters and other non-human anatomies. Keep age-appropriate depiction, including 17-year-old characters.
- Preserve existing masters and SHA; legacy 2.8–3.0-head sprites remain in use until replacements pass QA. No global runtime switch yet.
- Morwen canonical HD v2 is the first visual benchmark. The earlier restriction of her 7.5-head walk to a permanently separate HD-only track is lifted **as a long-term policy**; immediate work still uses DEV preview and a guarded rollout until map and NPC alignment is proven.

## Phased implementation
1. **Baseline**: inspect Aidan/Fiona/Morwen official master art, foot anchors, relative heights, collision boxes and current map tile/camera scaling. Define visual examples for adult human, teen, child, elderly, dwarf and fairy.
2. **Pilot**: finish Morwen left six-frame walk (10fps) and four-direction idle with common boot anchor; verify 69px hair-to-sole provisional display height against map and Aidan. Revisit actual CSS/world scale after map context comparison.
3. **Party**: develop Aidan, Fiona, and companions with consistent head-to-body ratio, height hierarchy and equipment silhouette; character-by-character QA.
4. **World**: optimize NPCs, enemies, doors, furniture, stairs, props, vegetation, architecture and perspective for new proportions, without replacing original art.
5. **Integration**: controlled feature flag, screenshot comparison, no regressions to field movement, occlusion, battle, SAVE or mobile viewport. Independent QA and Android checks required before main/public release.

## Acceptance gates
- 4 directions with consistent costume, scale, alpha/feet anchors, head count appropriate to each design; walk cycles show correct left/right-facing feet, no sliding/cropping.
- Map/doorway/furniture contact points, character overlap/occlusion, camera zoom, dialogue portraits, collision footprint and interaction range inspected at mobile and desktop viewports.
- Report before/after screenshots and separate known baseline FAILs from new FAILs. Android and independent QA are NOT_RUN until evidenced.

## Cross-reference
- `docs/design/FIELD_HD_PIXEL_OFFICIAL_PIPELINE.md` (earlier 2.8–3.0 rule superseded)
- `docs/design/morwen-hd-walk/MORWEN_HD_WALK_01_V2_DIRECTOR_DECISIONS.md` (its section 5 HD-only limitation superseded by this decision; DEV-first implementation gate remains)
- Draft game PR #221 and website PR #25; no merge or deployment authorized by this document.
