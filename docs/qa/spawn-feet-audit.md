# Z: 全マップspawn足元監査

STATUS READY / work/codex-tz / main d153d06。新規tools/qa/check_spawn_feet.pyと報告/JSON/ログのみ。ゲーム/マップ本体未変更。

本編28 + DEV2マップ、100個のspawn、動的collision flags全組み合わせを含め102条件。**全条件合格、FAILS0**。Footprintは実FieldCollisionの22×10、actor top-left=feet-(17,42)。world外とfootbox collisionを検査し、実FieldHeightがあるmapはspawn宣言またはderive/commit後の実levelで判定する。

旧家02の430,452が点ではfreeでもstoolへ足元で重なる負例と、472の正例を実APIで自己テスト。JSONは各条件のblocker id/flag/levelを含む。マップ修正の提案が必要なspawnは今回なし。

| map | scope | spawn | feet | effective level | flags | 結果 |
|---|---|---|---|---:|---|---|
| cliff_moher_01_spiral_ascent | main | from_lind (default) | 150,3658.3778132003163 | 0 | {} | 合格 |
| cliff_moher_01_spiral_ascent | main | summit | 2280,1262.3578904783485 | 0 | {} | 合格 |
| dev_height_proto | DEV | start (default) | 300,1250 | 0 | {} | 合格 |
| dev_height_proto | DEV | deck | 1560,600 | 1 | {} | 合格 |
| dev_height_proto | DEV | plateau | 2000,250 | 1 | {} | 合格 |
| dev_height_proto | DEV | under | 1560,900 | 1 | {} | 合格 |
| dev_monster_arena | DEV | center (default) | 2400,1600 | 0 | {} | 合格 |
| fort_dunvall_01_courtyard | main | from_tavern (default) | 710,990 | 0 | {} | 合格 |
| fort_dunvall_01_courtyard | main | from_road | 1600,2300 | 0 | {} | 合格 |
| fort_dunvall_01_courtyard | main | from_capital_road | 3050,1200 | 0 | {} | 合格 |
| fort_dunvall_01_courtyard | main | from_ramparts | 480,1100 | 0 | {} | 合格 |
| fort_dunvall_01_courtyard | main | from_keep | 1600,1080 | 0 | {} | 合格 |
| fort_dunvall_02_ramparts | main | from_courtyard (default) | 300,800 | 0 | {} | 合格 |
| fort_dunvall_02_ramparts | main | from_keep | 1400,300 | 0 | {} | 合格 |
| fort_dunvall_03_keep | main | from_courtyard (default) | 1200,1400 | 0 | {} | 合格 |
| fort_dunvall_03_keep | main | from_wall | 1820,860 | 0 | {} | 合格 |
| fort_in_tavern | main | from_courtyard (default) | 700,830 | 0 | {} | 合格 |
| moss_forest_01_sunlit_path | main | from_lind (default) | 1429.3,5672.9 | 0 | {} | 合格 |
| moss_forest_01_sunlit_path | main | from_area2 | 7559.4,489.5 | 0 | {} | 合格 |
| moss_forest_01_sunlit_path | main | from_cliff_fall | 2020,5043.6 | 0 | {} | 合格 |
| moss_forest_02_mossy_ravine | main | from_area1 (default) | 8396.5,6900.9 | 0 | {} | 合格 |
| moss_forest_02_mossy_ravine | main | from_area3 | 1658.5,276.8 | 0 | {} | 合格 |
| moss_forest_03_ancient_grove | main | from_area2 (default) | 840,6490 | 0 | {'moss_a3_seal_open': False} | 合格 |
| moss_forest_03_ancient_grove | main | from_area2 (default) | 840,6490 | 0 | {'moss_a3_seal_open': True} | 合格 |
| moss_forest_03_ancient_grove | main | dev_sanctuary | 4300,3140 | 0 | {'moss_a3_seal_open': False} | 合格 |
| moss_forest_03_ancient_grove | main | dev_sanctuary | 4300,3140 | 0 | {'moss_a3_seal_open': True} | 合格 |
| rilde_in_aidan | main | default (default) | 250,330 | 0 | {} | 合格 |
| rilde_in_aidan | main | from_village | 480,532 | 0 | {} | 合格 |
| rilde_in_aidan | main | from_bed | 250,330 | 0 | {} | 合格 |
| rilde_in_barn | main | default (default) | 500,512 | 0 | {} | 合格 |
| rilde_in_barn | main | from_village | 500,512 | 0 | {} | 合格 |
| rilde_in_elder | main | default (default) | 480,532 | 0 | {} | 合格 |
| rilde_in_elder | main | from_village | 480,532 | 0 | {} | 合格 |
| rilde_in_house_01 | main | default (default) | 430,452 | 0 | {} | 合格 |
| rilde_in_house_01 | main | from_village | 430,452 | 0 | {} | 合格 |
| rilde_in_house_02 | main | default (default) | 430,472 | 0 | {} | 合格 |
| rilde_in_house_02 | main | from_village | 430,472 | 0 | {} | 合格 |
| rilde_in_house_03 | main | default (default) | 430,452 | 0 | {} | 合格 |
| rilde_in_house_03 | main | from_village | 430,452 | 0 | {} | 合格 |
| rilde_in_house_04 | main | default (default) | 690,452 | 0 | {} | 合格 |
| rilde_in_house_04 | main | from_village | 690,452 | 0 | {} | 合格 |
| rilde_in_inn_1f | main | default (default) | 600,612 | 0 | {} | 合格 |
| rilde_in_inn_1f | main | from_village | 600,612 | 0 | {} | 合格 |
| rilde_in_inn_1f | main | from_stairs | 1000,330 | 0 | {} | 合格 |
| rilde_in_inn_2f | main | default (default) | 220,330 | 0 | {} | 合格 |
| rilde_in_inn_2f | main | from_stairs | 220,330 | 0 | {} | 合格 |
| rilde_in_shop | main | default (default) | 480,532 | 0 | {} | 合格 |
| rilde_in_shop | main | from_village | 480,532 | 0 | {} | 合格 |
| rilde_in_storage | main | default (default) | 380,412 | 0 | {} | 合格 |
| rilde_in_storage | main | from_village | 380,412 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_aidan | 1345,602 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_elder | 610,529 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_inn | 975,531 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_shop | 395,847 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_house_01 | 375,1182 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_house_02 | 685,1360 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_house_03 | 345,1527 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_house_04 | 665,1116 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_barn | 1195,964 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_storage | 1415,969 | 0 | {} | 合格 |
| rilde_village_01_peace | main | default (default) | 1345,660 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_cliff | 830,1552 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_fort | 2212,695 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_plaza | 1020,860 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_training | 1877,860 | 0 | {} | 合格 |
| rilde_village_01_peace | main | from_sunset | 830,1550 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_aidan | 1345,602 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_elder | 610,529 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_inn | 975,531 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_shop | 395,847 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_house_01 | 375,1182 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_house_02 | 685,1360 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_house_03 | 345,1527 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_house_04 | 665,1116 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_barn | 1195,964 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_storage | 1415,969 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | default (default) | 1345,660 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_cliff | 830,1552 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_fort | 2212,695 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_plaza | 1020,860 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_training | 1877,860 | 0 | {} | 合格 |
| rilde_village_01_ruin | main | from_sunset | 830,1550 | 0 | {} | 合格 |
| road_dunvall_capital_01 | main | from_fort (default) | 200,1900 | 0 | {} | 合格 |
| road_dunvall_capital_01 | main | from_capital | 5400,1800 | 0 | {} | 合格 |
| road_dunvall_capital_01 | main | overlook | 3800,900 | 0 | {} | 合格 |
| royal_capital_00_gate | main | from_guild (default) | 900,1090 | 0 | {} | 合格 |
| royal_capital_00_gate | main | from_inn | 3500,1090 | 0 | {} | 合格 |
| royal_capital_00_gate | main | from_road | 2200,3250 | 0 | {} | 合格 |
| royal_capital_00_gate | main | from_market | 2200,360 | 0 | {} | 合格 |
| royal_capital_00_gate | main | from_gate_inside | 2200,1650 | 0 | {} | 合格 |
| royal_capital_01_market | main | from_gate (default) | 2400,2850 | 0 | {} | 合格 |
| royal_capital_01_market | main | from_plaza | 2400,360 | 0 | {} | 合格 |
| royal_capital_01_market | main | from_residential | 360,1500 | 0 | {} | 合格 |
| royal_capital_01_market | main | from_craft | 4400,1500 | 0 | {} | 合格 |
| royal_capital_02_castle_plaza | main | from_market (default) | 2000,3300 | 0 | {} | 合格 |
| royal_capital_02_castle_plaza | main | from_residential | 360,1700 | 0 | {} | 合格 |
| royal_capital_02_castle_plaza | main | from_castle | 2000,1260 | 0 | {} | 合格 |
| royal_capital_02_castle_plaza | main | from_east | 3640,1700 | 0 | {} | 合格 |
| royal_capital_03_residential | main | from_market (default) | 360,1200 | 0 | {} | 合格 |
| royal_capital_03_residential | main | from_plaza | 3300,1500 | 0 | {} | 合格 |
| royal_in_guild | main | from_gate (default) | 900,920 | 0 | {} | 合格 |
| royal_in_inn | main | from_gate (default) | 700,830 | 0 | {} | 合格 |

未実施: 動的NPC/敵の重なり、画像の不透明部分との重なり、spawnからの到達性、transition即発火、旧セーブ位置、heightSpecs opt-in overlay。これはJSON本体の物理足元監査であり、見た目/所属面の意図/ストーリー到達を保証しない。DEVの曖昧XYはderiveで上面が選ばれ得る（underはlevel1になるがfoot collisionはfree）。

再実行: python3 tools/qa/check_spawn_feet.py --self-test / --out /tmp/spawn.json。Nodeで現在のfield-collision.js/field-height.jsを読む。出力だけを指定先へ保存、mapに書き込まない。失敗はexit1。

main変更なしでロールバック不要。次: 追加AAのoverlay draftとlint。
