# 全回帰結果（O）

source HEAD `64a7a56f1f250b57536f084004d50660e5f3bbdc` / main基準 `6e28466751f124fc5a483be3d89c65f35a320b5c`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m65_dev_up_walk.py | 新規 | 1 | 13.47 | 1 / [] | tests_moss_m65_dev_up_walk.py.log |
| tests/moss/m62_aidan_down_production.py | 合格 | 0 | 29.368 | 0 / [0] | tests_moss_m62_aidan_down_production.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 26.9 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 5.204 | 0 / [0] | tests_system_asset_registry_audit.py.log |
| tests/moss/m49_phase4_formal_adoption.py | 合格 | 0 | 0.429 | 0 / [0] | tests_moss_m49_phase4_formal_adoption.py.log |

集計: 合格 4, main既存 0, 新規 1, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
