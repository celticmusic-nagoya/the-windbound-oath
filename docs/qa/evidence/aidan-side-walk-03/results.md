# 全回帰結果（O）

source HEAD `c541efa11fe0ecce66288aae9c7205be64d9e26f` / main基準 `5523023306de776f0ce558e5486f4f4c675083f5`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m58_aidan_side_stride.py | 合格 | 0 | 43.66 | 0 / [0] | tests_moss_m58_aidan_side_stride.py.log |
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 56.569 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |
| tests/moss/m57_aidan_side_toes.py | 合格 | 0 | 31.586 | 0 / [0] | tests_moss_m57_aidan_side_toes.py.log |
| tests/system/aidan_side_toes.py | 合格 | 0 | 1.683 | 0 / [0] | tests_system_aidan_side_toes.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 25.63 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 18.736 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 5.946 | 0 / [0] | tests_system_asset_registry_audit.py.log |

集計: 合格 7, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
