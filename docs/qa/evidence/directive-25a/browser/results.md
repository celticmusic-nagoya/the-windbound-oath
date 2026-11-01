# 全回帰結果（O）

source HEAD `e70942ea6876f8f7409bf9040abedbd85d929f1e` / main基準 `5ab60c5db833821744d73080f91ffcd559ebf0a4`、port 8765、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/title_official_layout.py | 合格 | 0 | 72.475 | 0 / [0] | tests_system_title_official_layout.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 25.902 | 0 / [] | tests_system_save_continue_lifecycle.py.log |
| tests/moss/m6_scenario.py | 合格 | 0 | 8.461 | 0 / [] | tests_moss_m6_scenario.py.log |
| tests/moss/m7_cliff.py | 合格 | 0 | 36.632 | 0 / [] | tests_moss_m7_cliff.py.log |
| tests/moss/m12_attack_ruin.py | 合格 | 0 | 18.214 | 0 / [] | tests_moss_m12_attack_ruin.py.log |
| tests/moss/m18_moss_scenario.py | 合格 | 0 | 17.736 | 0 / [0] | tests_moss_m18_moss_scenario.py.log |
| tests/moss/m4_e2e.py | 合格 | 0 | 152.592 | 0 / [] | tests_moss_m4_e2e.py.log |
| tests/moss/m36_event_cg.py | 合格 | 0 | 380.25 | 0 / [0] | tests_moss_m36_event_cg.py.log |
| tests/moss/m20_sword_equipment.py | 合格 | 0 | 16.257 | 0 / [0] | tests_moss_m20_sword_equipment.py.log |
| tests/moss/m23_wind_dance_battle.py | 合格 | 0 | 72.312 | 0 / [0] | tests_moss_m23_wind_dance_battle.py.log |
| tests/moss/m15_slime.py | 合格 | 0 | 42.438 | 0 / [] | tests_moss_m15_slime.py.log |
| tests/moss/m15c_forest_bat.py | 合格 | 0 | 61.667 | 0 / [] | tests_moss_m15c_forest_bat.py.log |
| tests/moss/m15d_leafy_boar.py | 合格 | 0 | 73.496 | 0 / [] | tests_moss_m15d_leafy_boar.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 40.976 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m6_inventory.py | 合格 | 0 | 15.191 | 0 / [] | tests_moss_m6_inventory.py.log |
| tests/moss/m6_quest.py | 合格 | 0 | 8.026 | 0 / [] | tests_moss_m6_quest.py.log |
| tests/moss/m10_rilde.py | 合格 | 0 | 43.971 | 0 / [] | tests_moss_m10_rilde.py.log |
| tests/moss/m8_town_maps.py | 合格 | 0 | 290.78 | 0 / [] | tests_moss_m8_town_maps.py.log |
| tests/moss/m11_road_tavern.py | 合格 | 0 | 46.936 | 0 / [] | tests_moss_m11_road_tavern.py.log |
| tests/moss/m14_capital_gate.py | 合格 | 0 | 33.9 | 0 / [] | tests_moss_m14_capital_gate.py.log |
| tests/system/capital_story_test.py | 合格 | 0 | 34.107 | 0 / [] | tests_system_capital_story_test.py.log |
| tests/system/shop_flow_test.py | 合格 | 0 | 16.402 | 0 / [] | tests_system_shop_flow_test.py.log |
| tests/system/equipment_ui_flow_test.py | 合格 | 0 | 12.149 | 0 / [] | tests_system_equipment_ui_flow_test.py.log |
| tests/moss/m14_hold_move.py | 合格 | 0 | 16.694 | 0 / [] | tests_moss_m14_hold_move.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 19.03 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/moss/m32_lou_follower.py | 合格 | 0 | 11.592 | 0 / [0] | tests_moss_m32_lou_follower.py.log |
| tests/moss/m55_mobile.py | 合格 | 0 | 18.407 | 0 / [] | tests_moss_m55_mobile.py.log |
| tests/moss/m19_perf.py | 合格 | 0 | 97.839 | 0 / [] | tests_moss_m19_perf.py.log |
| tests/moss/m53_story_expression_assignment.py | 合格 | 0 | 60.79 | 0 / [0] | tests_moss_m53_story_expression_assignment.py.log |
| tests/moss/m54_dev_formal_status.py | 合格 | 0 | 22.503 | 0 / [0] | tests_moss_m54_dev_formal_status.py.log |
| tests/moss/m45_dev_portrait_test.py | 合格 | 0 | 35.398 | 0 / [0] | tests_moss_m45_dev_portrait_test.py.log |
| tests/moss/m49_phase4_formal_adoption.py | 合格 | 0 | 0.522 | 0 / [0] | tests_moss_m49_phase4_formal_adoption.py.log |
| tests/moss/m51_blink_formal_adoption_22a.py | 合格 | 0 | 0.372 | 0 / [0] | tests_moss_m51_blink_formal_adoption_22a.py.log |

集計: 合格 33, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
