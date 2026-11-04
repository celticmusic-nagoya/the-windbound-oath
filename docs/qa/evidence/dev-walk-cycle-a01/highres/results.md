# 全回帰結果（O）

source HEAD `9302902693c89f1938bcfc9fad4ee03f17cb9301` / main基準 `e63780543d7ba1719a39a2f68b9924dc6d5b3933`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m59_dev_down_cycle.py | 新規 | 1 | 13.864 | 1 / [] | tests_moss_m59_dev_down_cycle.py.log |
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 57.402 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |
| tests/moss/m58_aidan_side_stride.py | 合格 | 0 | 42.674 | 0 / [0] | tests_moss_m58_aidan_side_stride.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 24.976 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 5.143 | 0 / [0] | tests_system_asset_registry_audit.py.log |

集計: 合格 4, main既存 0, 新規 1, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
