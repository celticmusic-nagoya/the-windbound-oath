# ファイル担当・進捗索引

着手前にブランチと対象を追記する。別ブランチの記録もfetchして確認する。下記はCodex側の記録であり、Claudeの担当を予約しない。

| 担当 | ブランチ | 対象 | 状態 |
|---|---|---|---|
| Codex | work/codex-collaboration-rules | docs/handoff/COLLABORATION.md、CLAIMS.md、codex-collaboration-rules.md | READY: 運用資料のみ |
| Codex | work/codex-quality-foundation | 品質G: field-movement、tests、docs/art、docs/qa等（各branchの差分参照） | 開始基準でテスト合格、最新main再検証待ち |
| Codex | work/codex-loading-cg | docs/art/loading-cg/ | BLOCKED: 画像生成API利用上限、画像0枚 |
| Codex | work/codex-raider-mobile-layout | css/raider-mobile-layout.css、js/battle-party-layout.js、tests/battle/raider_mobile_layout.py、docs/qa/raider-mobile-layout/ | 開始基準でテスト合格、最新main再検証待ち |

Raiderブランチの既存index.html差分は、この新運用の受領前に作成済み（CSS link追加とscript cache query）。以降の直接編集は行わず、統合前にClaudeへ変更依頼として共有する。開始基準はe3565b6で、新main 0914263での再検証はまだ実施していない。
旧Codex Phase3は不採用。採用済みのClaude版へ旧素材・コードを戻さない。

## 承認済みRaider統合

Codex / `work/codex-raider-mobile-integration` / 基準main `0914263`。
対象: `8ac09e6` のCSS・BattlePartyLayout・テスト・QA資料、およびindexのCSS link／script cache queryだけ。作者がRaider修正を全承認済みのため、この限定index変更も統合する。Claudeのstory・field・納品motionは変更しない。
STATUS: READY — 最新main 0914263上で再検証完了。作者承認に基づきmainへ通常pushする。

## 依頼G移植(Claude, 2026-10-11)

Claude / `work/claude-port-quality-foundation` / 基準main `9b17d06`。
対象: Codex `work/codex-quality-foundation` の3コミット(59d0ce4 dae453c e89a936)を cherry-pick(衝突なし)。`field-movement.js`(frameScale下限)、`tests/run_all.sh`、`tests/run_python.py`、m55_hz、m6_quest、素材棚卸し資料。
共存確認: 長押し移動(`moss-forest-runtime.js` の hold / `hooks.onTransition`)は `FieldMovement.frameScale` を直接参照せず、`FieldNavigation.follow` を使うため変更なし。m14_hold_move と m55_hz が両方合格。Raider修正・納品戦闘モーションも維持。
全回帰(`./tests/run_all.sh`, 最新main+移植): **47件中46件合格**。`tests/lind/walk_intake.py` は全件実行時のみ一度失敗(負荷時のタイミング依存)し、単独再実行で合格。m6_quest は合格(Codexの修正による)。
STATUS: READY — 作者承認後に main へ。

## Codex: 依頼G再検証・m6_quest安定化 (2026-10-12)

Codex / `work/codex-quality-revalidation` / G基準 `65bf6d8`、main基準 `57dc6ae`。
対象: `tests/moss/m6_quest.py`、必要な回帰テスト、`docs/handoff/CLAIMS.md`、専用検証報告・QA結果。
STATUS: WIP — 最新mainとの統合候補をこのブランチで検証。mainへのmergeは作者承認後。
Claude `work/moss-slime-symbol-encounter` (`f80019e`) → `work/forest-bat-symbol-encounter` (`3259741`) → `work/leafy-boar-symbol-encounter` (`8baa264`) は積み重ねたPLAYER QA待ちブランチ。既存field-monsters/runtime/story/indexの担当変更は行わず、Gとの共存だけを検証する。
素材候補は別 `work/codex-art-redelivery-20261012` の `docs/art/` に保存予定。正式採用素材の置換・ゲームへの組み込みなし。

共存実行検証用 `work/codex-quality-symbol-validation` を本検証ブランチから作成予定。`8baa264` を仮統合し、CLAIMSの追記を双方保持して解決する。ゲームコードは担当差分をそのまま保持し、長押し・速度・王都遷移ゲート・m6_quest・敵3種・Raiderの既存テストで確認する。main統合候補とは別ブランチで、PLAYER QA承認済みとは扱わない。

2026-10-12 checkpoint: `f6f08bd` でm6_questのテスト側待機を安定化。修正前4回は今回すべて合格（申告の確率は今回未再現）、修正後10回連続合格。最新main+Gの全回帰は進行中。画像はHTTP429利用上限で0枚（専用報告参照）。王都出口IDは作者回答により未確定/TBD維持。Android実機は未接続・未測定、計測手順を保存（`docs/qa/android-symbol-performance-20261012.md`）。

依頼Cの3出口のtoMap/toSpawnとJSON存在確認は `docs/handoff/codex-capital-exit-receivers-20261012.md`。取得済み全リモートrefで受け側JSON未作成を確認。TBD/nullを維持し、マップJSON作成後に接続する。
