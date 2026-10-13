# MM セーブ互換性 / 不正データ耐性

基準mainf0fe968 / work/codex-ll-pp。新規tests/system/save_compat.pyと本報告/fixtures/results/logのみ。ゲーム/セーブ形式は変更しない。

## 結果

47検査: 合格37 / 失敗10 / 未実施0、uncaught pageerror0。失敗は新規発見として保持（FAILS10/exit1）。仕様の確認が必要なDEV保存ケースを含み、全てを製品の重大bugとは扱わない。

## fixtureの根拠

| version | 根拠 | 範囲 |
|---|---|---|
| 26/27 | git全履歴にこのversionのsaveGrowthData導入を確認できず | v28の最小キーを使った合成互換性probe。実在旧serializerの再現ではない |
| 28 | e0bd8d6 | 初回save導入。members/active/reserve/squads/support/gold/battleItems、prologueなし |
| 29 | 8c0b0de | root prologue追加、nested version1/forestChests/position(fpx/fpy含む) |
| 30 | 96c8a9f→9b20f6d→fd79182 | inventory/talk、quests、equipmentを加算。同じv30内の追加あり |

フィールド値は再現性のある現モデルから構成し、過去serializerのキー形状を再現した代表例。古い実ユーザーsaveをそのまま取得したものではない。fixtures.jsonに全入力/sourceを保存。

v26〜30の読み込み・成長/所持品保持・欠落inventory/装備/quest/talk既定値・Lou flag・旧forestChests→charm照合・v30通常map位置・木剣/単一accessory移行・読み込み時の元localStorage不変・正規化後v30再保存/再読込等価は合格。

## 指摘 / 再現

| ケース | 実測 | 優先度/提案 |
|---|---|---|
| malformed number-root | non-object/invalid root accepted | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed array-root | non-object/invalid root accepted | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed bad-level | invalid member level retained | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed numeric-level | invalid member level retained | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed negative-gold | invalid/negative gold retained | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed bad-potion | invalid item count retained | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed bad-support | non-boolean joined retained | loader前の型/ID検証・既定値/復元方針を検討 |
| malformed unknown-active | unknown active member retained | loader前の型/ID検証・既定値/復元方針を検討 |
| missing fields warm-load defaults | 現状stateが期待と不一致（JSON参照） | loader前の型/ID検証・既定値/復元方針を検討 |
| DEV height map/level roundtrip | 現状stateが期待と不一致（JSON参照） | loader前の型/ID検証・既定値/復元方針を検討 |

原JSON破損/nullはfalseを返して例外なし。根がnumber/arrayでもtrueを返す場合がある。member level文字列、負のgold、potion文字列、joined文字列、存在しないactive IDはlive stateへ保持される。joined='false'はBoolean変換ではtrueとなり、NNで救出前表示へつながる。

同じページでsupport=true/level4を読み込んだ後、support/membersのない旧形状をロードすると、その前の値が残る。ロード失敗時は全データを消すのではなく、検証済み状態を保持/安全な既定値を補う方針と、部分適用を避ける準備段階の検証を提案する（未実装）。

DEV height map/level保存はMossForestStory.fromSaveがA1〜A3だけを有効mapと判定するため、dev_height_proto/level1→A1/levelなしにfallback。DEV専用保持を保証するか作者判断。高さ無しA1の位置は保持できたが、本編全map/height保存が合格したとはしない。

再現: fixtures.jsonの該当dataをSAVE_KEYへ入れloadGrowthData。結果JSONのstateと照合。再実行 `python tests/system/save_compat.py`（自身の8832 server終了）。合成26/27は別記したため「確認済み過去実save5世代」とは報告しない。

変更ファイル/詳細証跡は [save-compat-20261013](save-compat-20261013/) 。Android実機未測定。次NNでLou表示との因果を確認。main未統合、戻し方（将来統合後）git revert -m 1 <merge>。
