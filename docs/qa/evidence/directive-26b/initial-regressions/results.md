# 全回帰結果（O）

source HEAD `dfdb4943735bbcd0685a238b2dbc5373f52fa2e7` / main基準 `ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3`、port 8765、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/early_rewards_26b.py | 合格 | 0 | 48.201 | 0 / [0] | tests_system_early_rewards_26b.py.log |
| tests/system/playable_audit_25a.py | 合格 | 0 | 109.043 | 0 / [0] | tests_system_playable_audit_25a.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 25.935 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/system/shop_flow_test.py | 合格 | 0 | 16.002 | 0 / [] | tests_system_shop_flow_test.py.log |
| tests/system/equipment_ui_flow_test.py | 合格 | 0 | 11.927 | 0 / [] | tests_system_equipment_ui_flow_test.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 41.006 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m6_quest.py | 合格 | 0 | 7.862 | 0 / [] | tests_moss_m6_quest.py.log |
| tests/moss/m6_scenario.py | 合格 | 0 | 9.499 | 0 / [] | tests_moss_m6_scenario.py.log |
| tests/moss/m53_story_expression_assignment.py | 合格 | 0 | 67.869 | 0 / [0] | tests_moss_m53_story_expression_assignment.py.log |
| tests/moss/m45_dev_portrait_test.py | 合格 | 0 | 34.711 | 0 / [0] | tests_moss_m45_dev_portrait_test.py.log |
| tests/moss/m49_phase4_formal_adoption.py | 合格 | 0 | 0.471 | 0 / [0] | tests_moss_m49_phase4_formal_adoption.py.log |
| tests/moss/m51_blink_formal_adoption_22a.py | 合格 | 0 | 0.377 | 0 / [0] | tests_moss_m51_blink_formal_adoption_22a.py.log |
| tests/system/asset_registry_audit.py | 合格 | 0 | 5.635 | 0 / [0] | tests_system_asset_registry_audit.py.log |

集計: 合格 13, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
