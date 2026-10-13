# Codex 指示 V〜Z (2026-10-13) — T/U に続く追加分
基準: 最新main。standing-orders に従う。ゲームのランタイムコード(js/)は変更しない(Claude側が編集中)。tests/tools/docs のみ。

## V: 最新main全回帰(O のrunner使用)
`work/codex-regression-runner` の runner で最新mainを全実行し、結果表を `docs/qa/full-regression-<date>.md` に。分類: 合格/失敗/未実施/main既存(m13,m4_e2e)/新規。新規失敗があれば即報告(原因の切り分けまで)。

## W: m13_elder_attack_text / m4_e2e の期待値更新案
古い台詞期待値で失敗している2本について、現行の台詞(index.html)に合わせた修正パッチ案を `docs/handoff/stale-tests-fix.patch` と説明で提示(テストだけ変更。ゲーム文言は変えない)。適用可否はClaudeが判断。

## X: Android実機パフォーマンス計測キット
高さ機能をメインマップで有効化する前提となる実機計測のため、ユーザーが Android で開くだけで計測できる手順を用意:
- `docs/qa/android-perf-protocol.md`(手順・合格基準案・結果の貼り付けテンプレ)
- 既存の perf-meter(dev)/ `tests/moss/m19_perf.py` の指標を調べ、実機で `?dev=1&perf=1` 等で表示/コピーできるか確認(新規実装が必要なら提案のみ)。
- 禁止: js/ の変更。

## Y: field-walkers の level 対応テスト設計
Rの指摘4。walker と home 会話ゾーンの面整合、上下同XYでの停止有無、height無しの従来挙動不変を検証するテスト(失敗してよい)を `tests/moss/m25_walkers_level.py` に。

## Z: 全28マップの spawn 22×10 足元衝突検査
Qの調査で見つかった「点ベース validator の見逃し」を全マップに拡張: `tools/qa/check_spawn_feet.py` で全 spawn の 22×10足元ボックスが非衝突か検査(実 FieldCollision を使う。tests/field/house02_spawn.test.js を参考)。結果表を `docs/qa/spawn-feet-audit.md` に。修正は提案のみ(マップデータは変更しない)。
