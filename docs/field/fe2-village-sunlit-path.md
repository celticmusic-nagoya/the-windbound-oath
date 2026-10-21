# F-E2: 平時のリルド村 ⇄ 陽だまりの道（A1）接続

- 開放条件: storyStage 1〜3（フィオナ合流 = `#fiona` クリックで stage 0→1 の後〜断崖到達前）。stage 0 は案内トースト、stage 4〜14、襲撃後（ruin）、stage 15 以降は閉鎖。
  - **stage 15 以降の村北ルートは閉鎖維持で正式決定済み（2026-10-21）。再開放はこの PR の範囲外。**
- 村: `tr_v_to_moss` rect(770,48,120,60) / spawn `from_moss_forest` (830,190,down)。peace/ruin 両方（spawn 名集合は同一）。北道を塞いでいた木 `tree_10` は生成時に除外。
- A1: `tr_to_lind` は `RildeVillage.exit()` が処理（`from_moss_forest` へ）。stage 0〜8 の天候は clear、平時は通常ゴブリン（`type:goblin`）を出さない（`hooks.monsterAllowed`。stage 9+ の挙動は不変）。
- 襲撃後の落下先 A2（滝つぼ南岸 (1150,4040)）は**未実装**（別 PR）。

## 生成元メモ
- 村 JSON は `tools/moss/build_rilde_village.py` から再生成（`prepare_rilde_lind.py && make_rilde_art.py && build_rilde_village.py`）。再生成すると `rilde_in_house_02.json` の末尾改行と `img/field/moss/manifest.json` の並び順だけが変わる（既存の無関係な差分。コミットしない）。
- **A1 の runtime JSON（`data/maps/moss_forest_01_sunlit_path.json`）は設計 JSON（`tools/moss/design/…`）の `export_runtime.py` 出力とは一致しない**（props 40→78、treasure 4→5、`weather`、`timeOfDay` は runtime 側にのみある。`place_additional_assets.py` など後工程が runtime JSON を直接更新）。F-E2 はこの runtime JSON に 2 点だけ直接パッチした: ① `weather.rules` 先頭に `{when:{stage:[0,8]},set:'clear',ms:0}`、② `tr_to_lind.note`。設計 JSON からの再エクスポートは既存の `weather` 等も消すため、元々禁止の運用。守り: `tests/moss/fe2_village_sunlit_roundtrip.py` が ① を検証する。

## セーブ・ロード（別課題）
平時（stage ≤ 8）に A1 でセーブしても、ロード時に A1 へは復帰しない（stage ≤ 8 のロードは旧 DOM の位置復元。村フィールドでのセーブも同様）。F-E2 では未対応のまま。進行不能・データ破損は起きない（テストで確認）。別 issue として扱う。

## 回帰テスト結果の切り分け（Claude Code 自己テスト。Codex 独立QAではない）
- 全回帰（main 3365826 + 本ブランチ）: Executed=91 Failed=2。
- 失敗 2 件（`tests/battle/lou_idle_real_flow.py`、`tests/moss/m9_env.py`）は、**main 対照・本ブランチとも単独で 3/3 PASS**。全回帰中のみ失敗＝負荷（同時に画像レンダリングを実行していた）によるタイミング依存の失敗と判断（環境要因。`m9_env` は天候遷移待ちのため同様と推定、厳密な原因は未確定）。F-E2 由来の失敗は確認されていない。
- `m10_flow` の exit 1 は、全回帰を二重起動しポート 8765 が競合した run でのみ発生。単独の全回帰では PASS、再現せず。
- `m33b` のキー移動判定は main でも不安定（既存問題）。
