# 少年剣士 (rv_boy_swordsman) official frames — ASSET-EMMA-01

Replaced: `img/field/moss/rilde/npc/boy_swordsman_idle.png`, `boy_swordsman_f01..f06.png` (map, manifest, NPC id, talk table, event zone, collision, 7 fps: unchanged).
Source: the supplied 6-frame sheet, 1536x1024 RGBA. **Only the chat-attachment copy was available (original file not verifiable).** Not committed to the repo (no original PNG overwritten).
Per-frame source rects, foot anchors and output bboxes: `boy_swordsman_export_map.json`.

- Cut: individual alpha bounding boxes (alpha>4, connected components) — the wind effects of frames 2/3/4 cross the 512-px grid, so an even 3x2 split would clip them. No frame touches the output canvas edge.
- Export: 288x256 RGBA (2x of the old 144x128, same 9:8 as the display box 72x64), scale 0.47 (character height matches the old 46-px NPC), premultiplied-alpha area downscale (no halos), **feet anchored at x=146,y=252** in every frame (boots midpoint; +2 px = the old +1 world-px offset `dx`).
- **Mirrored**: the walker is drawn with `scaleX(-1)` (dir -1) and the old placeholder faced right, so the left-facing official art is exported mirrored to keep him facing left in game. (A pure flip of the supplied frames; nothing redrawn.)
- Order 1→6 (reading order: guard, overhead raise, wind slash, wind slash, guard, raise). 6→1 repeats at the loop point.
- idle = copy of f05 (guard stance, no effect); the old idle was pixel-art and would clash.
- Shared legacy art `img/field/lind/npc/villagers/boy_swordsman_*` (old DOM village) is untouched.
- `tools/moss/prepare_rilde_lind.py` regenerates these files from the legacy frames; it now skips `boy_swordsman` images while `boy_swordsman.OFFICIAL` exists.
- source copy kept at docs/art/source/boy_swordsman_sheet_COPY_1536x1024.png (sha256 in SHA256.txt); it is a copy, not the original file.
