# 全回帰結果（O）

source HEAD `fb2bfff68291921a5c5d80c91d0bda8e0f5805ff` / main基準 `169f197bafd0511475253649c16b6916aa738165`、port 8801、直列、各test自前server、timeout 600秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/battle/hero_motion_plan.py | 合格 | 0 | 0.432 | 0 / [] | tests_battle_hero_motion_plan.py.log |
| tests/battle/hit_sync.py | 合格 | 0 | 12.473 | 0 / [0] | tests_battle_hit_sync.py.log |
| tests/battle/lou_idle_loop.py | 合格 | 0 | 39.879 | 0 / [0] | tests_battle_lou_idle_loop.py.log |
| tests/battle/motion_intake.py | 合格 | 0 | 7.572 | 0 / [] | tests_battle_motion_intake.py.log |
| tests/battle/raider_mobile_layout.py | 合格 | 0 | 63.736 | 0 / [] | tests_battle_raider_mobile_layout.py.log |
| tests/field/fisherman.test.js | 合格 | 0 | 0.171 | 0 / [] | tests_field_fisherman.test.js.log |
| tests/field/frame_clock.test.js | 合格 | 0 | 0.173 | 0 / [] | tests_field_frame_clock.test.js.log |
| tests/field/house02_spawn.test.js | 合格 | 0 | 0.138 | 0 / [] | tests_field_house02_spawn.test.js.log |
| tests/field/m0.test.js | 合格 | 0 | 1.075 | 0 / [] | tests_field_m0.test.js.log |
| tests/field/npc_registry.test.js | 合格 | 0 | 0.17 | 0 / [] | tests_field_npc_registry.test.js.log |
| tests/field/talk_conditions.test.js | 合格 | 0 | 0.17 | 0 / [] | tests_field_talk_conditions.test.js.log |
| tests/input/kb_battle.py | 合格 | 0 | 36.776 | 0 / [0] | tests_input_kb_battle.py.log |
| tests/input/kb_field.py | 合格 | 0 | 13.622 | 0 / [0] | tests_input_kb_field.py.log |
| tests/input/kb_menu.py | 合格 | 0 | 12.06 | 0 / [0] | tests_input_kb_menu.py.log |
| tests/input/kb_raider.py | 合格 | 0 | 9.258 | 0 / [0] | tests_input_kb_raider.py.log |
| tests/input/kb_scene.py | 合格 | 0 | 13.963 | 0 / [0] | tests_input_kb_scene.py.log |
| tests/lind/walk_intake.py | 合格 | 0 | 19.098 | 0 / [] | tests_lind_walk_intake.py.log |
| tests/moss/m10_flow.py | 合格 | 0 | 64.094 | 0 / [] | tests_moss_m10_flow.py.log |
| tests/moss/m10_rilde.py | 合格 | 0 | 38.466 | 0 / [] | tests_moss_m10_rilde.py.log |
| tests/moss/m11_dev_lazy.py | 合格 | 0 | 33.693 | 0 / [] | tests_moss_m11_dev_lazy.py.log |
| tests/moss/m11_road_tavern.py | 合格 | 0 | 43.368 | 0 / [] | tests_moss_m11_road_tavern.py.log |
| tests/moss/m12_attack_ruin.py | 合格 | 0 | 15.457 | 0 / [] | tests_moss_m12_attack_ruin.py.log |
| tests/moss/m13_elder_attack_text.py | 合格 | 0 | 5.547 | 0 / [] | tests_moss_m13_elder_attack_text.py.log |
| tests/moss/m14_capital_gate.py | 合格 | 0 | 30.973 | 0 / [] | tests_moss_m14_capital_gate.py.log |
| tests/moss/m14_hold_move.py | 合格 | 0 | 13.867 | 0 / [] | tests_moss_m14_hold_move.py.log |
| tests/moss/m15_slime.py | 合格 | 0 | 39.417 | 0 / [] | tests_moss_m15_slime.py.log |
| tests/moss/m15b_slime_symbol.py | 合格 | 0 | 100.904 | 0 / [] | tests_moss_m15b_slime_symbol.py.log |
| tests/moss/m15c_forest_bat.py | 合格 | 0 | 58.936 | 0 / [] | tests_moss_m15c_forest_bat.py.log |
| tests/moss/m15d_leafy_boar.py | 合格 | 0 | 70.381 | 0 / [] | tests_moss_m15d_leafy_boar.py.log |
| tests/moss/m16_battle_feel.py | 合格 | 0 | 38.004 | 0 / [] | tests_moss_m16_battle_feel.py.log |
| tests/moss/m17_dev_arena.py | 合格 | 0 | 26.434 | 0 / [] | tests_moss_m17_dev_arena.py.log |
| tests/moss/m18_moss_scenario.py | 合格 | 0 | 13.967 | 0 / [0] | tests_moss_m18_moss_scenario.py.log |
| tests/moss/m19_height_proto.py | 合格 | 0 | 265.3 | 0 / [0] | tests_moss_m19_height_proto.py.log |
| tests/moss/m19_perf.py | 合格 | 0 | 88.787 | 0 / [] | tests_moss_m19_perf.py.log |
| tests/moss/m19_plan_bench.py | 合格 | 0 | 10.213 | 0 / [] | tests_moss_m19_plan_bench.py.log |
| tests/moss/m20_sword_equipment.py | 合格 | 0 | 8.615 | 0 / [0] | tests_moss_m20_sword_equipment.py.log |
| tests/moss/m21_wind_dance.py | 合格 | 0 | 6.052 | 0 / [0] | tests_moss_m21_wind_dance.py.log |
| tests/moss/m22_height_contacts.py | 合格 | 0 | 35.243 | 0 / [0] | tests_moss_m22_height_contacts.py.log |
| tests/moss/m23_wind_dance_battle.py | 合格 | 0 | 60.513 | 0 / [0] | tests_moss_m23_wind_dance_battle.py.log |
| tests/moss/m24_height_contacts_e2e.py | 合格 | 0 | 70.088 | 0 / [0] | tests_moss_m24_height_contacts_e2e.py.log |
| tests/moss/m26_height_spec_overlay.py | 合格 | 0 | 16.698 | 0 / [0] | tests_moss_m26_height_spec_overlay.py.log |
| tests/moss/m28_aidan_walk_assets.py | 合格 | 0 | 8.068 | 0 / [0] | tests_moss_m28_aidan_walk_assets.py.log |
| tests/moss/m29_leafy_boar_assets.py | 合格 | 0 | 21.098 | 0 / [0] | tests_moss_m29_leafy_boar_assets.py.log |
| tests/moss/m30_raider_dodge.py | 合格 | 0 | 40.749 | 0 / [0] | tests_moss_m30_raider_dodge.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 21.062 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/moss/m32_lou_follower.py | 合格 | 0 | 9.868 | 0 / [0] | tests_moss_m32_lou_follower.py.log |
| tests/moss/m4_devjump.py | 合格 | 0 | 30.423 | 0 / [] | tests_moss_m4_devjump.py.log |
| tests/moss/m4_e2e.py | 合格 | 0 | 174.105 | 0 / [] | tests_moss_m4_e2e.py.log |
| tests/moss/m4_npc.py | 合格 | 0 | 3.537 | 0 / [] | tests_moss_m4_npc.py.log |
| tests/moss/m4_save.py | 合格 | 0 | 13.904 | 0 / [] | tests_moss_m4_save.py.log |
| tests/moss/m55_chest.py | 合格 | 0 | 15.294 | 0 / [] | tests_moss_m55_chest.py.log |
| tests/moss/m55_cine.py | 合格 | 0 | 12.593 | 0 / [] | tests_moss_m55_cine.py.log |
| tests/moss/m55_hz.py | 合格 | 0 | 21.373 | 0 / [] | tests_moss_m55_hz.py.log |
| tests/moss/m55_mobile.py | 合格 | 0 | 12.589 | 0 / [] | tests_moss_m55_mobile.py.log |
| tests/moss/m6_asset_swap.py | 合格 | 0 | 9.876 | 0 / [] | tests_moss_m6_asset_swap.py.log |
| tests/moss/m6_devui.py | 合格 | 0 | 10.431 | 0 / [] | tests_moss_m6_devui.py.log |
| tests/moss/m6_inventory.py | 合格 | 0 | 11.271 | 0 / [] | tests_moss_m6_inventory.py.log |
| tests/moss/m6_quest.py | 合格 | 0 | 4.448 | 0 / [] | tests_moss_m6_quest.py.log |
| tests/moss/m6_scenario.py | 合格 | 0 | 5.8 | 0 / [] | tests_moss_m6_scenario.py.log |
| tests/moss/m6_talk.py | 合格 | 0 | 4.947 | 0 / [] | tests_moss_m6_talk.py.log |
| tests/moss/m7_choreo.py | 合格 | 0 | 17.141 | 0 / [] | tests_moss_m7_choreo.py.log |
| tests/moss/m7_cliff.py | 合格 | 0 | 35.197 | 0 / [] | tests_moss_m7_cliff.py.log |
| tests/moss/m7_prop_swap.py | 合格 | 0 | 14.236 | 0 / [] | tests_moss_m7_prop_swap.py.log |
| tests/moss/m8_town_maps.py | 合格 | 0 | 285.425 | 0 / [] | tests_moss_m8_town_maps.py.log |
| tests/moss/m9_env.py | 合格 | 0 | 66.135 | 0 / [0] | tests_moss_m9_env.py.log |
| tests/moss/m9_hero.py | 合格 | 0 | 12.923 | 0 / [0] | tests_moss_m9_hero.py.log |
| tests/moss/m9_hero_intake.py | 合格 | 0 | 30.935 | 0 / [0] | tests_moss_m9_hero_intake.py.log |
| tests/moss/scatter.test.js | 合格 | 0 | 0.826 | 0 / [] | tests_moss_scatter.test.js.log |
| tests/moss/seal_a3.py | 合格 | 0 | 202.123 | 0 / [] | tests_moss_seal_a3.py.log |
| tests/moss/walk_a1.py | 合格 | 0 | 39.819 | 0 / [] | tests_moss_walk_a1.py.log |
| tests/moss/walk_map.py | 合格 | 0 | 72.417 | 0 / [] | tests_moss_walk_map.py.log |
| tests/system/capital_story_test.py | 合格 | 0 | 32.697 | 0 / [] | tests_system_capital_story_test.py.log |
| tests/system/equipment_test.py | 合格 | 0 | 3.139 | 0 / [] | tests_system_equipment_test.py.log |
| tests/system/equipment_ui_flow_test.py | 合格 | 0 | 8.609 | 0 / [] | tests_system_equipment_ui_flow_test.py.log |
| tests/system/shop_flow_test.py | 合格 | 0 | 11.908 | 0 / [] | tests_system_shop_flow_test.py.log |

集計: 合格 75, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
