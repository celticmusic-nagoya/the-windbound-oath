# 全回帰結果（O）

source HEAD `a1ba70a576b2f504f9bc03bffb881ddfc5c58c83` / main基準 `2276c3c693cce9ea215dd68d51e1725bfb4e51fb`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m54_goblin_field20.py | 合格 | 0 | 36.514 | 0 / [0] | tests_moss_m54_goblin_field20.py.log |
| tests/system/goblin_field_assets.py | 合格 | 0 | 0.425 | 0 / [] | tests_system_goblin_field_assets.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 5.288 | 0 / [0] | tests_system_asset_registry_audit.py.log |

集計: 合格 3, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
