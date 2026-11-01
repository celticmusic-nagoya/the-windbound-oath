# 全回帰結果（O）

source HEAD `1af0b66eb0851d89d06aa321eb113506ffaddfdf` / main基準 `ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3`、port 8765、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/early_rewards_26b.py | 合格 | 0 | 44.196 | 0 / [0] | tests_system_early_rewards_26b.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 41.408 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m53_story_expression_assignment.py | 合格 | 0 | 62.324 | 0 / [0] | tests_moss_m53_story_expression_assignment.py.log |

集計: 合格 3, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
