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

## Claude: フィールド敵AI／シンボルエンカウント（PLAYER QA待ち）

Claude / `work/moss-slime-symbol-encounter` / 基準main `57dc6ae`。
対象: `js/field/field-monsters.js`（新規）、`moss-forest-runtime.js`（FieldMonsters接続・歩数エンカウント既定OFF）、`moss-forest-story.js`（onMonster）、`index.html`（script追加・撃破後resolve）、A1 JSON `monsters`（スライム2体）、`tests/moss/m15b_slime_symbol.py`。
STATUS: PLAYER QA待ち。作者承認までmainへmergeしない。モススライム／ゴブリンの速度等は `MONSTER_TYPES` の1か所で調整可能。

Claude / `work/forest-bat-symbol-encounter`（上記ブランチの上に積む）: フォレストバット（吸血・飛行シンボル、A2）。`work/leafy-boar-symbol-encounter`（さらにその上）: リーフィボア（突進シンボル、街道）。いずれもPLAYER QA待ち・main未merge。

## main反映記録
- 2026-10-12 Claude: フィールドモンスター一式（スライム/ゴブリン型AI・フォレストバット・リーフィボア）をmainへ `--no-ff` merge。ロールバック: タグ `rollback/before-field-monsters-20261012`（= 57dc6ae）、または該当マージコミットを `git revert -m 1`。PLAYER QA待ち。
- 2026-10-12 Claude: `work/battle-feel-and-monster-layout` — 戦闘演出（近接は選択敵位置へ飛び込み／フィオナは少し前進+魔弾／ルーの飛び回り+浮き沈み `js/battle-lou-flight.js`／カットイン `battle-presentation.js` durations 1250/2000ms・勝利ポーズ `VICTORY_POSE_MS=2400`）と、A1（スライム2・ボア2・ゴブリン2）／A2（スライム2・ボア2・バット2）配置、通常ゴブリンのフィールド戦闘接続（`fieldGobN`）。対象: index.html（WBActors v064/v066・finish）、js/battle-presentation.js、js/prologue-combat.js、js/field/moss-forest-story.js、css/battle-presentation.css、A1/A2 JSON、tests/moss/m16_battle_feel.py。
