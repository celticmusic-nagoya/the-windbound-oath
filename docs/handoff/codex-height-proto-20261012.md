# Codex 指示書: 高さプロトタイプ(Phase 1)の並行作業

作成: 2026-10-12 / 発注: Claude(統括) / 基準ブランチ: `feat/field-height-prototype`(WIP push 済み)

## 0. 背景(1分で読める版)
- 2.5D フィールド立体化の Phase 1 として、独立テストマップ `dev_height_proto` で「高さレイヤー(level)」を検証している。
- 仕様の正本は `js/field/field-height.js` 冒頭のコメント。マップ JSON の `height` キーと、`collision.blockers[].levels` が新スキーマ。
- 本編のマップ・セーブ・進行・戦闘は一切変更しない。Phase 1 は main にマージしない。

## 1. 作業ルール(厳守)
1. `feat/field-height-prototype` から `work/codex-height-<task>` ブランチを切って作業する。force push 禁止。main へのマージはしない。
2. **触ってはいけないファイル**(Claude が編集中): `js/field/field-height.js` / `field-navigation.js` / `field-collision.js` / `forest-loader.js` / `moss-forest-runtime.js` / `data/maps/dev_height_proto.json` / `tools/moss/build_height_proto.py` / `tests/moss/m19_*`。
3. 触ってよいのは、各依頼の「成果物」に書いた新規ファイルと、`index.html` の script タグ 1 行のみ。
4. 本編マップ(`data/maps/` のうち `dev_*` 以外)・セーブ形式・ストーリー進行・戦闘・採用済みキャラクター素材は変更しない。
5. 完了したら、ブランチ名・コミット ID・実行したコマンドと結果を報告する。未実施の項目は「未検証」と明記する。

## 2. 依頼A: 高さ検証ツール `tools/moss/check_levels.py`(新規)
目的: level をまたいだ到達可能性と、すり抜けの有無をマップデータから機械的に検証する。

- 入力: `data/maps/*.json` のうち `height` キーを持つマップのみ。持たないマップは無視する。
- 座標系: 「足元基準」。足元ボックスは 22×10 px(`js/field/field-collision.js` の `footprint`)。`height.levels[N].walk`、`connectors[].rect`、`collision.blockers[].levels` の意味は `field-height.js` 冒頭コメントを参照。コードは読むだけで変更しない。
- 検査内容:
  1. 各 level の歩行可能領域を足元ボックスで格子化(16px 格子)し、connector 経由でどの level 間が到達可能かを幅優先探索で出す。
  2. level 1 以上の領域が、connector 以外の場所で level 0 とつながっていない(すり抜けがない)ことを確認する。
  3. `eventZones` / `treasurePoints` / `spawns` / `transitions` の座標が、少なくとも 1 つの level で歩行可能であることを確認する。
  4. 同じ XY で複数の level が歩行可能な地点(橋の上下など)を一覧にする。
- 出力: 人が読める要約と、`--json` で機械可読の結果。問題があれば終了コード 1、なければ 0。`height` を持つマップが 1 つもない場合は何もせず 0。
- 書き方は `tools/moss/check_assets.py` に合わせる(`python3 tools/moss/check_levels.py [map_id ...]`)。
- 受け入れ条件: `dev_height_proto` に対して実行して問題 0 件。意図的に壊した複製データ(connector を削る、walk 矩形を広げる)で終了コード 1 になることを自分で確かめ、手順を報告する。

## 3. 依頼B: 計測用ページ機能 `?perf=1` と手順書
目的: Android 実機で性能を測り、その結果をそのまま貼れるようにする。

- 成果物: `js/dev/perf-meter.js`(新規)、`docs/qa/android-height-perf.md`(新規)、`index.html` に script タグ 1 行(`window.WINDBOUND_DEV` が真のときだけ動くこと。本番表示には何も出さない)。
- 画面の隅に表示する項目: FPS(平均 / 最小 / 1% ロー)、フレーム時間、`FieldNavigation.status.milliseconds`、JS ヒープ(取得できる場合)。
- 「60 秒計測して JSON をコピー」ボタン。JSON には、端末の UA、画面サイズ、devicePixelRatio、マップ ID、level、各指標を含める。
- 手順書: 端末の記録欄(機種、Android / Chrome のバージョン、解像度、更新 Hz、向き、回線、電源・発熱)と、**3 条件 × 各 3 回**(`dev_height_proto`、モス A2、リルド村)の結果表。体裁は `docs/qa/android-symbol-performance-20261012.md` に合わせる。
- 受け入れ条件: PC の Chromium で `?dev=1&perf=1` を開き、表示とコピーが動く。`?perf=1` なしでは何も表示されない。実機では動かせないので、実機の結果は「未検証」と書くこと。

## 4. 依頼C(任意、余力があれば): 既存テストの退行確認の下準備
- `tests/moss/` の全スクリプトを 1 本ずつ順に実行する小さなランナー `tests/moss/run_all.sh` を新規に作る(同時実行しない。`seal_a3` は 2〜3 分かかる)。
- 各スクリプトの終了コードと所要時間を一覧で出力する。既知の不安定テスト(`m6_quest` など)は、失敗してもランナーを止めず、一覧で「既知の不安定」と注記する。

## 5. 報告フォーマット
1. ブランチ名とコミット ID
2. 変更ファイル一覧(新規 / 変更)
3. 実行したコマンドと結果(成功・失敗の別)
4. 未検証の項目と理由
5. 気づいた問題や、Claude への質問
