# 全回帰結果（O）

source HEAD `fbafe47064b1d453f46a302073ddac8ebba3ee56` / main基準 `2f5312efdfd4f5ad48439dd5bca17bb0b801bffc`、port 8765、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 24.833 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/system/title_official_layout.py | 合格 | 0 | 67.032 | 0 / [0] | tests_system_title_official_layout.py.log |
| tests/moss/m53_story_expression_assignment.py | 合格 | 0 | 63.708 | 0 / [0] | tests_moss_m53_story_expression_assignment.py.log |
| tests/moss/m45_dev_portrait_test.py | 合格 | 0 | 34.651 | 0 / [0] | tests_moss_m45_dev_portrait_test.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 41.234 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m49_phase4_formal_adoption.py | 合格 | 0 | 0.673 | 0 / [0] | tests_moss_m49_phase4_formal_adoption.py.log |
| tests/moss/m51_blink_formal_adoption_22a.py | 合格 | 0 | 0.427 | 0 / [0] | tests_moss_m51_blink_formal_adoption_22a.py.log |
| tests/system/asset_registry_audit.py | 新規 | 1 | 2.236 | 2 / [2] | tests_system_asset_registry_audit.py.log |
| tests/system/playable_audit_25a.py | 新規 | 1 | 108.594 | 4 / [4] | tests_system_playable_audit_25a.py.log |

集計: 合格 7, main既存 0, 新規 2, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
