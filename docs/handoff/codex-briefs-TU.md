# Codex 指示 T / U (2026-10-13)
基準: 最新main(c909ed1以降)。standing-orders に従う。ゲームコードは変更しない(テスト/ツール/ドキュメントのみ)。

## T: 風の舞・魔弾MPの実エンジン計測
main には 風の舞(`?feature=windDanceCommand` + 習得)と魔弾MP回復(`?boltMana=hit|action`)が実装済み(実装メモ: docs/handoff/wind-dance-implementation-20261013.md、テスト: tests/moss/m23_wind_dance_battle.py)。
- 成果物: `tools/sim/engine_wind_dance_bench.py`(Playwright, 自前server, 直列)と `docs/handoff/wind-dance-engine-bench.md` + 結果JSON。
- 対象戦闘: レイダー戦(`startRaiderBattle`系)と通常戦(`fieldGob1` 等、ID は m23 参照)。
- 条件: ①風の舞なし ②風の舞あり・魔弾MP回復なし ③あり・`boltMana=hit` ④あり・`boltMana=action`。
- 方針: 固定方針ボット(Aidan: 攻撃、Fiona: 風の舞が切れていてMP>=10なら風の舞、それ以外は魔弾)。ランダム要素(回避・会心)は seed 固定 or 200試行以上の平均。
- 出力: 戦闘終了時MP、撃破ターン(ラウンド数)、勝敗(敗北は『ルーの風が時間を巻き戻す』経路も記録)、被ダメ合計、回避発生数、Fiona の支援/魔弾回数。
- 禁止: 数値・ゲームコード変更。最終数値は報告のみ(推奨は「回復3」暫定を踏まえて)。

## U: 接触レベル対応の追加テスト(失敗テストでよい)
R の指摘(docs/qa/height-contact-impl-review.md)を受け、Claude が runtime を修正中。次を `tests/moss/m24_height_contacts_e2e.py` として作成(まだ失敗してよい/該当機能が無いものは `SKIP:` と理由を明示):
- 有効な feet(例 1560,900 など blockedAtLevel==false を各配置前に assert)で、上下同XYの NPC/宝箱/草むら/story symbol/動く敵/出口/rest/ambience。
- once・報酬・戦闘開始の回数(hook call 回数)で副作用の漏れがないこと。
- 橋外 ground の player → 橋下 NPC をタップ → 目的地の level が対象 level であること。
- 接触遅延中に階変更 → 戦闘開始 0。
- 縦390×844/横844×390 で上階オブジェクトのタップ位置。
- 失敗時は sys.exit(1)、console error も収集。
- 禁止: runtime/map の変更。
