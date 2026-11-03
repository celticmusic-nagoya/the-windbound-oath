# Intermediate tester independent browser QA

Exact tested HEAD `600fd784bd16867abf865cc2ab82a6965c57f44d`.

**Representative UI PASS; not a final merge gate after external main22efe87.**

Executed96 checks across1920×1080,390×844,844×390 with actual DEV entry, Aidan/goblin/NPC selectors, stepping/play/pause, measured0.5-to2 playback-rate change, all4 computed background colors, exact idle selection, honest missing NPC up direction, reduced-motion, close cleanup and unchanged SAVE/flags/stock/player position. Saved NPC/goblin UI screenshots. Separate active-patrol check explicitly observed statewalk at open, froze exact position/clock/wait/state750ms, closed and observed resume; LOAD and battle takeover clear the inspector and animation request.

Reviewed full root matrix and regression raw logs:1185frame slots PASS;10 product/browser regressions PASS, archive-historyless asset freshness failure retained and correctly superseded by history-enabled PASS. Prior source5ca→600JS/CSS/tests unchanged. Source/image-identical new soldier data was independently checked at PR107 exact7fd4b68, and new PR112 exact964b2a5 runtime/m31 PASS is separately retained.

The earlier401probe was stopped due external main change and is not counted as a final PASS. Root will merge external Aidan change then reconcile production stride72. Final exact-head focused stride/source gate is still required. Browser closed and released. No product/main/PR changes were made by independent reviewer.
