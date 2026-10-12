# 高さプロトタイプ Phase 1 最終報告(2026-10-12)
**状態: 未完了(Android実機の性能が未検証のため)。mainにはマージしていない。**
ブランチ `feat/field-height-prototype`(統合後 45ba8bc〜)

## 1. 実装した機能と変更ファイル
- 高さレイヤー(level)を実行時のキャラ状態として保持。段差の通行は connector(階段/坂/橋のスロープ)の端点帯だけで切り替わり、意図しない落下はない。
- 新規: `js/field/field-height.js`、`data/maps/dev_height_proto.json`(開発専用)、`tools/moss/build_height_proto.py`、`tests/moss/m19_height_proto.py`、`m19_perf.py`、`m19_plan_bench.py`、`tools/moss/check_levels.py`、`js/dev/perf-meter.js`、`tests/moss/run_all.sh`、各種 docs。
- 変更(高さを持たない既存マップの挙動は不変): `field-collision.js`(blockers の `levels`)、`field-navigation.js`(高さ対応A*)、`forest-loader.js`、`moss-forest-runtime.js`、`index.html`(script追加・DEV開始メニュー1行)。
- 本編のマップ/進行/戦闘/セーブ形式/採用済みキャラ素材は未変更。

## 2. プロトタイプの操作
`?dev=1` → DEVメニューから「高さプロトタイプ(2.5D)」。通常と同じ(矢印/WASD、タップ移動)。足元に `level` 表示。専用操作なし。

## 3. 階段・坂・橋・崖
m19(PC/縦/横 計85項目)全合格。階段・坂で level が端点帯で切り替わる、崖と水際で level 0 からは登れない、橋の上下(同一XY)が別 level として区別される、橋の下を通る level 0 の歩行(橋脚は通行不可)、橋の下で床板が半透明化。

## 4. 高さ対応の経路探索
高さをまたぐタップ移動(低地→橋上、低地→高台、高台→低地)と橋下横断が合格。Codexのベンチ(各10回): 遠距離 1×CPUで中央値 約13〜17ms、4×CPUで約47〜75ms(2D遠距離 6.5ms / 24ms)。最適化前(約200ms / 約750ms)から大幅に改善。表: `plan-bench.md`。

## 5. スクリーンショット
`docs/qa/field-height-proto/` の `<view>_03_under_bridge`(橋の下)、`03b_on_deck_same_xy`(橋の上・同一XY)、`06_behind_tree`(前景遮蔽)ほか(pc/portrait/landscape)。

## 6. 性能(ヘッドレスChromium・クラウド。実機ではない)
| 条件 | 画面 | dev_height_proto 平均FPS / p99 | Moss A2 平均FPS |
| --- | --- | --- | --- |
| 1× | pc / 縦 / 横 | 54.9 / 55.8 / 55.3 | 15.8(初回ウォーム不足の外れ値) / 49.7 / 47.3 |
| 4×CPU | pc / 縦 / 横 | 34.6 / 42.7 / 42.5 | 15.7 / 24.9 / 22.4 |
経路計画: 1×で20〜50ms、4×で107〜128ms(長距離タップ1回)。**Android実機は未検証。** 手順書 `android-height-perf.md`(`?dev=1&perf=1`)で3条件×3回の計測を要する。

## 7. 既存テスト
- m19 85/85(3画面)。`check_levels.py dev_height_proto`: 問題0。
- `tests/moss/` 全体の掃引: 失敗は m13 / m4_e2e のみ(いずれも main でも同じ台詞期待値で失敗=既存の問題。長老の朝の台詞が4番目になった、森到着の台詞文言が変わった)。m55_hz は発生ごとの揺らぎで、Codex の単独実行では main・高さブランチとも合格。
- Aidan 歩行素材差し替え後の m10_flow / m14_hold_move / m7_choreo / m16_battle_feel は合格。

## 8. セーブ互換の最終提案
- 本編セーブ(`prologue.moss = {map,x,y,opened,fired}`)に任意の `level`(省略時0)を追加。読み込み時 `level` が無ければ `derive()`(XYから推定)にフォールバック。橋のようにXYが曖昧な場所は保存された level を優先。saveGrowthData は version 30 → 31、旧セーブは無変更で読める。
- 本編マップへの適用は Phase 2 以降。今回はプロトタイプ内(`heightState()` の往復)のみ検証。

## 9. 問題点と残課題
- 未検証: Android実機の性能、実機でのタッチ操作。**これが済むまで Phase 1 は完了としない。**
- イベントゾーン・敵・NPC・宝箱は level 非対応(`eventZones` に任意の `level` を追加する案、他レベルのNPC/敵との接触判定は未実装・未検証)。
- 橋の床板の占有XYをタップすると、橋の下に居る場合を除き最上位 level を選ぶ。
- 同行者(フィオナ)は主人公の足跡を追う方式で level を持つ。
- 素材はプレースホルダー。Phase 2 素材仕様書: `docs/art/height_asset_requests.md`。

## 10. コミット
`feat/field-height-prototype`: 528f46e(WIP)、45ba8bc(Codex D/E/F+A/B/C統合)、以降本報告。Codex: `work/codex-height-tools` 22b256e、`work/codex-height-analysis` 1e85618。
