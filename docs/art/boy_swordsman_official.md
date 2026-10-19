# 少年剣士 (rv_boy_swordsman) official frames — blond 10-year-old design (ASSET-EMMA-01 / swordsman)

Replaces: `img/field/moss/rilde/npc/boy_swordsman_idle.png`, `boy_swordsman_f01..f06.png` (map, manifest, NPC id, talk table, event zone, collision, 7 fps: unchanged).
**Supersedes the earlier export** (brown-haired / green-wrap design, from a different sheet): that design is not the adopted one. Old sheet copy removed from the tree (still in git history).
Source: the adopted 6-frame sheet, 1536x1024 RGBA, sha256 `2adb834cca781207e7f39c70361cbd032a84d28522b10438fc1b11c456ff8e83` (docs/art/source/…COPY…; **chat-attachment copy, original file not verifiable**). Export tool: `tools/art/export_boy_swordsman_official.py`; per-frame rects/anchors: `boy_swordsman_export_map.json`.

- Frame order (sheet reading order = the specified order): 01 Ready, 02 Raise, 03 High Guard, 04 Downswing, 05 Follow-through, 06 Recovery -> loop 6 -> 1. idle = Ready (copy of f01).
- Background: the sheet has real alpha (max 254, no fully opaque pixel) but a soft brown glow around each figure (partial alpha) and the glows of the top/bottom rows overlap. Cut per figure: core = alpha>=200 component, edge band = core dilated 20 px, alpha = smoothstep(110..235) of the source alpha inside the band; specks not attached to the core dropped. Result: no glow, hair/sword/wrist guards intact, no frame touches the canvas edge (`docs/art/boy_swordsman_official_cut_preview_magenta.jpg`).
- Export: 288x256 RGBA (2x the 144x128 canvas / 72x64 display box), scale 0.40 (body ~189 px = ~47 px on screen; old placeholder 45.5), premultiplied-alpha area downscale, feet anchored at (146,252) (midpoint of the two boots) in every frame.
- Facing: the art faces right (head/ear/torso), like the old placeholder; the walker mirrors with `scaleX(-1)` for dir -1, so he faces left in the village exactly as before. **No mirror baked in.**
- In-game check: `docs/art/boy_swordsman_ingame_loop_strip.jpg` (7 consecutive frames next to the training dummy).
- Shared legacy art `img/field/lind/npc/villagers/boy_swordsman_*` (old DOM village) is untouched. `tools/moss/prepare_rilde_lind.py` skips `boy_swordsman` images while `boy_swordsman.OFFICIAL` exists.
- Known: foot anchor differs by up to 1 px (2x) between frames; wide stance means the anchor is the boot midpoint, not a single foot.
