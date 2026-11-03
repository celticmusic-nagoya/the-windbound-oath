# 全回帰結果（O）

source HEAD `85e6e1be7e1adcd02525a549ed90d7987bfca572` / main基準 `12b1dca9433f6c2f2b69c2a63c097ad95fdc5e2b`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/aidan_side_toes.py | 合格 | 0 | 1.847 | 0 / [0] | tests_system_aidan_side_toes.py.log |
| tests/moss/m57_aidan_side_toes.py | 合格 | 0 | 36.027 | 0 / [0] | tests_moss_m57_aidan_side_toes.py.log |
| tests/moss/m55_dev_walk_motion.py | 合格 | 0 | 165.974 | 0 / [0] | tests_moss_m55_dev_walk_motion.py.log |
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 58.963 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 25.796 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 18.347 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 6.089 | 0 / [0] | tests_system_asset_registry_audit.py.log |

集計: 合格 7, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
