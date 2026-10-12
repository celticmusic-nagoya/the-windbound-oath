# Codex 指示書(第2弾): 退行の切り分け・経路探索ベンチ・Phase 2 素材仕様

作成: 2026-10-12 / 発注: Claude(統括) / 前回: `docs/handoff/codex-height-proto-20261012.md`(依頼A/B/C は納品済み)

## 0. 共通ルール(前回と同じ)
1. `feat/field-height-prototype` の最新から `work/codex-height-<task>` を切る。force push 禁止。main へのマージはしない。
2. **触ってはいけないファイル**(Claude が編集中): `js/field/field-height.js` / `field-navigation.js` / `field-collision.js` / `forest-loader.js` / `moss-forest-runtime.js` / `data/maps/dev_height_proto.json` / `tools/moss/build_height_proto.py` / `tests/moss/m19_*`。
3. 本編マップ・セーブ形式・ストーリー進行・戦闘・採用済みキャラクター素材は変更しない。
4. 報告: ブランチ名、コミット ID、実行コマンドと結果、未検証の項目と理由。

## 1. 依頼D(最優先): 既存テスト失敗の「main で起きるか」の切り分け
背景: 高さプロトタイプのブランチで `tests/moss/` を順に実行したところ、次の3本が失敗した。このブランチの変更が原因か、main でも起きる既存の問題かを切り分けたい。

| テスト | 失敗内容 |
| --- | --- |
| `m13_elder_attack_text.py` | 「peaceful elder cycles to the morning line」が失敗 |
| `m4_e2e.py` | 300 秒でタイムアウト(以前からの既知の問題の可能性) |
| `m55_hz.py` | 失敗(詳細は未確認) |

手順:
1. `git worktree add /tmp/main-wt origin/main`(main の `0d48324` 以降)を作り、そこで別ポート(例 8766)の静的サーバーを立てる。`PORT=8766` を付けて 3 本を実行する。
2. 同じ 3 本を、`feat/field-height-prototype` の最新でも実行する。
3. 他のテストと**同時に実行しない**(過去に同時実行で `m4_save` が失敗した)。各テストは単独で、1 本ずつ順に。
4. 結果を表にする: テスト名 × (main / プロトタイプブランチ) × (成功 / 失敗 / タイムアウト) × 失敗メッセージの要点。
5. main でも失敗するものは、原因を調べて原因候補を 3 行以内で書く。**修正はしない**(修正案があれば別ブランチで差分だけ提示)。プロトタイプブランチでだけ失敗するものは、最小の再現手順を書く。

受け入れ条件: 3 本すべてについて、main とプロトタイプブランチの結果が表で比較されていること。

## 2. 依頼E: 経路探索ベンチ `tests/moss/m19_plan_bench.py`(新規)
背景: 高さ対応の経路探索(`FieldHeight.plan`)は、遠距離タップで PC でも約 200 ms、CPU 4 倍低速で約 750 ms かかった。既存の 2D 探索(`FieldNavigation` の `plan`)との比較表を作りたい。

- 対象は Playwright(Chromium)。`dev_height_proto` で、次の 5 経路について、プランナーを直接呼んで所要時間(ms)と展開ノード数を測る。各経路 10 回、中央値と最大値を出す。
  1. 低地の近距離(300,1250)→(500,1250)
  2. 低地→橋の上(1560,600)
  3. 低地→高台(2000,250)
  4. 高台→低地(300,1250)
  5. 橋の下 level 0 の横断(1450,900)→(1700,900)
- 比較用に、高さを持たない既存マップ(`moss_forest_02_mossy_ravine`)で、同程度の距離の 2D 探索を 3 経路測る(`FieldNavigation.destination` と `follow` の 1 回目の呼び出し時間でよい)。
- CPU スロットリング(Playwright の CDP `Emulation.setCPUThrottlingRate` で 1 倍と 4 倍)の両方で測る。
- 結果を JSON と Markdown の表で出力する(`docs/qa/field-height-proto/plan-bench.md`)。
- 受け入れ条件: 5+3 経路 × 2 条件の結果が表になっていること。コードは読むだけで変更しない(`window.FieldHeight` と `window.FieldNavigation` の公開 API だけを使う)。

## 3. 依頼F: Phase 2 用の素材仕様書 `docs/art/height_asset_requests.md`(新規、ドキュメントのみ)
目的: Phase 1 が承認された後、ChatGPT(画像生成)に出す素材依頼の下書きを先に作る。コードは変更しない。

- 対象素材(現状はプレースホルダーの色ブロック): 崖の正面(岩壁 / 苔むした遺跡の石積み)、石段(昇り方向別)、緩やかな坂、橋の床板、橋の欄干、橋脚、高台の縁、前景の樹冠。
- 各素材について、次を表にする: 用途、推奨サイズ(px、`unitScale 2.5` と現在の 56 px の高さ段差に合わせる)、タイリングの有無、背景透過の要否、足元基準(アンカー)、昼夕夜の色補正への耐性、既存の画風(`docs/art/chatgpt_moss_forest_map_brief.md` と `docs/art/chatgpt_moss_asset_prompts.md`)との整合メモ。
- ChatGPT 用のプロンプト例(日本語)を素材ごとに 1 つ付ける。既存プロンプトの書式(`docs/art/chatgpt_moss_asset_prompts.md` の §1-2 / §1-8)に合わせる。
- 採用済みのキャラクター素材や既存の納品アセットを指示・変更しない。
- 受け入れ条件: 上記の全素材が表とプロンプト例つきで揃っていること。

## 4. 報告フォーマット
1. ブランチ名とコミット ID
2. 変更ファイル一覧(新規 / 変更)
3. 実行したコマンドと結果
4. 未検証の項目と理由
5. 気づいた問題と Claude への質問
