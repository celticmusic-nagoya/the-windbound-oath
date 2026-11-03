# 全回帰結果（O）

source HEAD `9ddf5fa92cb97e2b22583805302c88130d9029b7` / main基準 `3d1794340feb7210f209ae4beea2dc879034e92f`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 65.42 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |
| tests/moss/m55_dev_walk_motion.py | 新規 | 1 | 180.378 | 1 / [] | tests_moss_m55_dev_walk_motion.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 26.632 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 18.776 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 6.441 | 0 / [0] | tests_system_asset_registry_audit.py.log |
| tests/system/goblin_field_assets.py | 合格 | 0 | 0.423 | 0 / [] | tests_system_goblin_field_assets.py.log |

集計: 合格 5, main既存 0, 新規 1, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
