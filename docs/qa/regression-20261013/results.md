# 全回帰結果（O）

source HEAD `58df9f7ceb7de6b742f5e48a9fe8dc45b3265de6` / main基準 `53180f3e9932c320f9929c9ef66eddb08eeb6fa7`、port 8783、直列、各test自前server、timeout 600秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/battle/hero_motion_plan.py | 合格 | 0 | 0.486 | 0 / [] | tests_battle_hero_motion_plan.py.log |
| tests/battle/hit_sync.py | 合格 | 0 | 12.382 | 0 / [0] | tests_battle_hit_sync.py.log |
| tests/battle/motion_intake.py | 合格 | 0 | 7.464 | 0 / [] | tests_battle_motion_intake.py.log |
| tests/battle/raider_mobile_layout.py | 合格 | 0 | 62.722 | 0 / [] | tests_battle_raider_mobile_layout.py.log |
| tests/field/fisherman.test.js | 合格 | 0 | 0.17 | 0 / [] | tests_field_fisherman.test.js.log |
| tests/field/frame_clock.test.js | 合格 | 0 | 0.17 | 0 / [] | tests_field_frame_clock.test.js.log |
| tests/field/m0.test.js | 合格 | 0 | 1.022 | 0 / [] | tests_field_m0.test.js.log |
| tests/field/npc_registry.test.js | 合格 | 0 | 0.138 | 0 / [] | tests_field_npc_registry.test.js.log |
| tests/field/talk_conditions.test.js | 合格 | 0 | 0.151 | 0 / [] | tests_field_talk_conditions.test.js.log |
| tests/lind/walk_intake.py | 合格 | 0 | 18.395 | 0 / [] | tests_lind_walk_intake.py.log |
| tests/moss/m10_flow.py | 合格 | 0 | 64.025 | 0 / [] | tests_moss_m10_flow.py.log |
| tests/moss/m10_rilde.py | 合格 | 0 | 37.998 | 0 / [] | tests_moss_m10_rilde.py.log |
| tests/moss/m11_dev_lazy.py | 合格 | 0 | 33.475 | 0 / [] | tests_moss_m11_dev_lazy.py.log |
| tests/moss/m11_road_tavern.py | 合格 | 0 | 43.126 | 0 / [] | tests_moss_m11_road_tavern.py.log |
| tests/moss/m12_attack_ruin.py | 合格 | 0 | 15.1 | 0 / [] | tests_moss_m12_attack_ruin.py.log |
| tests/moss/m13_elder_attack_text.py | main既存 | 1 | 5.444 | 1 / [] | tests_moss_m13_elder_attack_text.py.log |
| tests/moss/m14_capital_gate.py | 合格 | 0 | 30.931 | 0 / [] | tests_moss_m14_capital_gate.py.log |
| tests/moss/m14_hold_move.py | 合格 | 0 | 13.678 | 0 / [] | tests_moss_m14_hold_move.py.log |
| tests/moss/m15_slime.py | 合格 | 0 | 39.344 | 0 / [] | tests_moss_m15_slime.py.log |
| tests/moss/m15b_slime_symbol.py | 合格 | 0 | 99.581 | 0 / [] | tests_moss_m15b_slime_symbol.py.log |
| tests/moss/m15c_forest_bat.py | 合格 | 0 | 59.005 | 0 / [] | tests_moss_m15c_forest_bat.py.log |
| tests/moss/m15d_leafy_boar.py | 合格 | 0 | 69.989 | 0 / [] | tests_moss_m15d_leafy_boar.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 37.904 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m17_dev_arena.py | 合格 | 0 | 26.364 | 0 / [] | tests_moss_m17_dev_arena.py.log |
| tests/moss/m18_moss_scenario.py | 合格 | 0 | 14.08 | 0 / [0] | tests_moss_m18_moss_scenario.py.log |
| tests/moss/m19_height_proto.py | 合格 | 0 | 266.056 | 0 / [0] | tests_moss_m19_height_proto.py.log |
| tests/moss/m19_perf.py | 合格 | 0 | 88.428 | 0 / [] | tests_moss_m19_perf.py.log |
| tests/moss/m19_plan_bench.py | 合格 | 0 | 9.912 | 0 / [] | tests_moss_m19_plan_bench.py.log |
| tests/moss/m20_sword_equipment.py | 合格 | 0 | 8.308 | 0 / [0] | tests_moss_m20_sword_equipment.py.log |
| tests/moss/m21_wind_dance.py | 合格 | 0 | 5.744 | 0 / [0] | tests_moss_m21_wind_dance.py.log |
| tests/moss/m4_devjump.py | 合格 | 0 | 30.14 | 0 / [] | tests_moss_m4_devjump.py.log |
| tests/moss/m4_e2e.py | main既存 | 1 | 169.227 | 1 / [] | tests_moss_m4_e2e.py.log |
| tests/moss/m4_npc.py | 合格 | 0 | 3.485 | 0 / [] | tests_moss_m4_npc.py.log |
| tests/moss/m4_save.py | 合格 | 0 | 13.434 | 0 / [] | tests_moss_m4_save.py.log |
| tests/moss/m55_chest.py | 合格 | 0 | 15.196 | 0 / [] | tests_moss_m55_chest.py.log |
| tests/moss/m55_cine.py | 合格 | 0 | 12.308 | 0 / [] | tests_moss_m55_cine.py.log |
| tests/moss/m55_hz.py | 合格 | 0 | 20.963 | 0 / [] | tests_moss_m55_hz.py.log |
| tests/moss/m55_mobile.py | 合格 | 0 | 12.423 | 0 / [] | tests_moss_m55_mobile.py.log |
| tests/moss/m6_asset_swap.py | 合格 | 0 | 9.591 | 0 / [] | tests_moss_m6_asset_swap.py.log |
| tests/moss/m6_devui.py | 合格 | 0 | 10.026 | 0 / [] | tests_moss_m6_devui.py.log |
| tests/moss/m6_inventory.py | 合格 | 0 | 11.147 | 0 / [] | tests_moss_m6_inventory.py.log |
| tests/moss/m6_quest.py | 合格 | 0 | 4.189 | 0 / [] | tests_moss_m6_quest.py.log |
| tests/moss/m6_scenario.py | 合格 | 0 | 5.757 | 0 / [] | tests_moss_m6_scenario.py.log |
| tests/moss/m6_talk.py | 合格 | 0 | 5.046 | 0 / [] | tests_moss_m6_talk.py.log |
| tests/moss/m7_choreo.py | 合格 | 0 | 17.091 | 0 / [] | tests_moss_m7_choreo.py.log |
| tests/moss/m7_cliff.py | 合格 | 0 | 34.856 | 0 / [] | tests_moss_m7_cliff.py.log |
| tests/moss/m7_prop_swap.py | 合格 | 0 | 14.041 | 0 / [] | tests_moss_m7_prop_swap.py.log |
| tests/moss/m8_town_maps.py | 合格 | 0 | 285.112 | 0 / [] | tests_moss_m8_town_maps.py.log |
| tests/moss/m9_env.py | 合格 | 0 | 65.559 | 0 / [0] | tests_moss_m9_env.py.log |
| tests/moss/m9_hero.py | 合格 | 0 | 12.543 | 0 / [0] | tests_moss_m9_hero.py.log |
| tests/moss/m9_hero_intake.py | 合格 | 0 | 29.527 | 0 / [0] | tests_moss_m9_hero_intake.py.log |
| tests/moss/scatter.test.js | 合格 | 0 | 0.725 | 0 / [] | tests_moss_scatter.test.js.log |
| tests/moss/seal_a3.py | 合格 | 0 | 201.776 | 0 / [] | tests_moss_seal_a3.py.log |
| tests/moss/walk_a1.py | 合格 | 0 | 39.862 | 0 / [] | tests_moss_walk_a1.py.log |
| tests/moss/walk_map.py | 合格 | 0 | 72.168 | 0 / [] | tests_moss_walk_map.py.log |
| tests/system/capital_story_test.py | 合格 | 0 | 32.784 | 0 / [] | tests_system_capital_story_test.py.log |
| tests/system/equipment_test.py | 合格 | 0 | 3.038 | 0 / [] | tests_system_equipment_test.py.log |
| tests/system/equipment_ui_flow_test.py | 合格 | 0 | 8.457 | 0 / [] | tests_system_equipment_ui_flow_test.py.log |
| tests/system/shop_flow_test.py | 合格 | 0 | 11.739 | 0 / [] | tests_system_shop_flow_test.py.log |

集計: 合格 57, main既存 2, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
