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
- 新規 `fe2_village_sunlit_roundtrip.py`: 旧版は「キーを固定時間だけ押す」ため、低速な環境（負荷・CPU制限）で3往復目の出口に届かず FAIL し得た（テスト側のタイミング依存。ゲーム側は8往復・CPU 8倍低速でも正常）。現版は目的（出口矩形/マップ遷移）に着くまで押し続ける。アサーションは不変（到達しなければ後続の判定が FAIL する）。stage 0 の会話ブロックは入力再試行ではなく前提アサーションで扱う。main では 9 件 FAIL（検出力あり）、本PRでは 68 PASS（通常・負荷時とも）。
- `tests/battle/lou_idle_real_flow.py`（戦闘待機のコマ観測、3秒窓）: **本PR無関係の既存の不安定テスト**。main（3365826）単独でも 6 回中 3 回 FAIL（本ブランチ 2/6）で、FAIL 時の観測列も同一（サンプル12件で 0/2/3/5 のみ=サンプリング間隔が粗く、1・4コマを拾えない）。戦闘・待機コードは本PRで未変更。アサーションは未変更。
- `m9_env`: baseでも再現する既存の挙動。本PR固有ではない。
- `m10_flow` の exit 1 は、全回帰を二重起動しポート 8765 が競合した run でのみ発生。
- `m33b` のキー移動判定は main でも不安定（既存問題）。
- 攻撃イベント各段階（devJump: training/sunset/attack/reunion/north/escape/forest/altar）と LOAD（stage 0〜15 の保存→再読込）: main と本ブランチで結果が同一（stage 保持・コンソールエラー 0）。stage 8 の LOAD で `rilde_in_aidan` が一時的に有効になる揺らぎは main でも出る（起動競合の既存課題 Issue #20）。保存データは疑似セーブ（`PrologueProgress.serialize()`）での確認で、実セーブUI経由ではない。
