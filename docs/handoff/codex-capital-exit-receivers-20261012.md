# 依頼C: 王都3出口の受け側確認

基準mainコミット: `57dc6aebc817b4255cf72cb907ab0623547b62b8`
ブランチ: `work/codex-quality-revalidation`
変更ファイル一覧: 本報告とCLAIMSのみ。出口設定・生成元・マップJSONは変更なし。
追加・変更したID・フラグ: なし。
テスト結果: fetch後の56リモートref（origin/HEADを含む）の `data/maps/*.json` を調査。83種類のmap blobを読み、ファイル名・map ID・表示名・spawn定義を確認。受け側の職人/騎士団/大聖堂/魔法学術/王城内マップを確認できなかった。
未実装・要確認: 受け側マップJSONとspawnの実装・作者確認後にClaude側で接続。
STATUS: BLOCKED — RECEIVER MAPS NOT CREATED

## 報告表

| 既存出口ID | 接続方向 | toMap（受け側map ID） | toSpawn（受け側spawn名） | マップJSONのブランチ上の存在 |
|---|---|---|---|---|
| `tr_r1_to_craft` | 市場東 → 職人地区 | `TBD`（未確定） | `TBD`（未確定） | 受け側未作成。取得済み全リモートrefで確認できず |
| `tr_r2_to_east` | 広場東 → 騎士団/大聖堂/魔法学術地区 | `TBD`（未確定） | `TBD`（未確定） | 受け側未作成。取得済み全リモートrefで確認できず |
| `tr_r2_castle_gate` | 広場北 → 王城内 | `TBD`（未確定） | `TBD`（未確定） | 受け側未作成。取得済み全リモートrefで確認できず |

これは接続用の確定値ではなく、現在の生成済み出口の値。`tools/moss/capital_exits.json` は3項目とも `null` を維持する。作者からも未確定のため保留との回答あり。

## 誤接続を避けるための確認

- `data/maps/royal_capital_01_market.json` に市場東出口、`data/maps/royal_capital_02_castle_plaza.json` に広場東/北出口が存在し、3項目とも `toMap: "TBD"`, `toSpawn: "TBD"`。
- main、G移植、スライム・バット・ボアの各ブランチにも受け側JSONはない。Codex側の取得済みブランチにも該当JSONを確認できず。
- `royal_capital_02_castle_plaza` は既存の城前広場（送り側）。その `from_castle` / `from_east` は広場に戻るためのspawnであり、王城内や東側地区の受け側ではない。
- Loading CG計画の `capital_craft` / `capital_knights` 等は予定CGのキー。実装済みmap IDやJSONとして流用しない。

## 接続できる状態になる条件

1. 受け側担当が `data/maps/<toMap>.json` と `spawns.points[<toSpawn>]` を含むブランチ・コミットを共有。
2. 実ファイルとspawnの存在、通行・復路・ストーリー条件を確認して、この表を確定値で更新。
3. Claudeが `tools/moss/capital_exits.json` に値を設定し、担当生成元から生成・検証する。

`tools/moss/build_town_maps.py` の `_disk_spawn()` はJSONが無い場合またはspawnが無い場合にエラーを返す。IDだけ先に設定しても接続は成立しない。本確認では生成物を書き換える生成スクリプトは実行していない。
