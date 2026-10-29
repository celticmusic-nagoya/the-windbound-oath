# DIRECTIVE-19B: normal portraits formally adopted2026-10-29

The user explicitly adopted these exact3 existing PNGs on2026-10-29 in DIRECTIVE-19B. No further confirmation is required. This supersedes the missing-approval blocker in [19A audit](PHASE4_ADOPTION_AUDIT.md) **only for these normal PNGs**; the historical audit is preserved unchanged. Other21 expressions are unapproved. Blink overlays are not registered; all3 are still portraits.

| Character | Source commit | SHA256 | Production file |
|---|---|---|---|
| フィオナ | `2020e558447f05791fb0c514d8e3b58c991302c5` | `89efd67352ac7f03882242d2363a2a2c8762bc0489e447a7d6089745a227094a` | `assets/images/characters/portraits/fiona/fiona_normal.png` |
| ルー | `2020e558447f05791fb0c514d8e3b58c991302c5` | `c2cc6d70614b18c685ef773e27bf4f50a7ed2947cb6e6b9367a5ba9e32e59e8f` | `assets/images/characters/portraits/lou/lou_normal.png` |
| エマ | `f4456a824adaa9add17204a8cd90385530f23619` | `f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2` | `assets/images/characters/portraits/emma/emma_normal.png` |

Images are byte-identical to the specified source commits. No alpha cleanup, crop export, regeneration or recompression. Crop rectangles are renderer-only: Fiona130,45,840,840; Lou0,0,1312,1199 (full wings/body); Emma90,0,880,880. These retain the old established source framing and were inspected against the exact approved PNGs. Source alpha254 is preserved where present.

## Production conversations

- Fiona: after training, summit bench at風見の断崖; the invitation to watch the sunset. Narration/choice page hides her; decline preserves flags/stage.
- Emma: first conversation with the existing Emma NPC in peacefulリルド村. Existing cycle/quest conditions are unchanged; later quest-priority conversations are not newly modified.
- Lou: after Raider victory, existing aftermath conversation. Explicit portrait metadata covers only the9 Lou-speaking pages; all narration/other speakers hide her. The strings, line indices, click/keyboard flow, join flag/stage13→14 and transition timer are unchanged.

Lou's conversation is a pre-existing custom text scene, not a FieldTalk table. The common `TalkPortrait.open(owner,{scene,anchor})` option places the same canvas above its existing text box; no character-specific renderer or new story event is introduced. Scene-hide/LOAD/battle/CG/cancel revoke ownership and invalidate late image requests.

DEV reads the registry: normal only for each of these3, `未実装・静止画`, motion buttons disabled. Aidan retains all6 expressions and48 blink overlays. Pending21 images are neither copied nor requested.

QA evidence and exact checked head are recorded on the implementation PR; Android physical QA remains user-pending.
