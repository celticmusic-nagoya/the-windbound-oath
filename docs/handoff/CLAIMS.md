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
STATUS: WIP — 最新main上で再検証後に通常push。
