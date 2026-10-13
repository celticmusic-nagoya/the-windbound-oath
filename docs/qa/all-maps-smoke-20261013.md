# OO 全30フィールドマップ巡回スモーク

基準mainf0fe968 / work/codex-ll-pp。m35_all_maps_smoke.pyと本報告/JSON/ログのみ、マップ/ゲームは未編集。

30map×Lou合流有無×昼夜=120条件完了。動的case合格120 / 失敗0 / 未実施0、pageerror/console event 0。遷移先JSONの存在確認は未解決11件（TBD8、hook-owned lind_village3）。FAILS11/exit1を保持。これを11個の新規ランタイム破損と同一視しない。

## マップ別

読み込み時間はMossForest.enterの完了までのwall clock、同一browserのcacheを共有。ネットワーク実機時間ではない。初期の明るさ/暗さ設定は即時、AIは凍結して戦闘に入らないスモーク。高さoverlayは本編既定OFF、inline DEV高度は通常loaderのまま。デフォルトspawnのみで、全spawnや出口を実際に歩いた試験ではない。

| map | 合格条件/4 | load min〜max ms | default blocked | 最大Fiona/Lou距離px |
|---|---:|---:|---|---:|
| cliff_moher_01_spiral_ascent | 4/4 | 918.1〜979.8 | False | 51.3/nan |
| dev_height_proto | 4/4 | 759.1〜792.9 | False | 16.0/2465.9 |
| dev_monster_arena | 4/4 | 758.3〜763.1 | False | 51.3/2188.2 |
| fort_dunvall_01_courtyard | 4/4 | 768.7〜806.9 | False | 51.3/1704.9 |
| fort_dunvall_02_ramparts | 4/4 | 765.0〜776.5 | False | 51.3/375.9 |
| fort_dunvall_03_keep | 4/4 | 762.8〜774.4 | False | 51.3/1157.9 |
| fort_in_tavern | 4/4 | 758.5〜780.1 | False | 51.3/723.9 |
| moss_forest_01_sunlit_path | 4/4 | 850.3〜891.5 | False | 51.3/4873.4 |
| moss_forest_02_mossy_ravine | 4/4 | 886.0〜935.2 | False | 51.3/7180.8 |
| moss_forest_03_ancient_grove | 4/4 | 845.2〜884.3 | False | 51.3/7455.1 |
| rilde_in_aidan | 4/4 | 753.3〜754.6 | False | 51.3/6221.3 |
| rilde_in_barn | 4/4 | 754.3〜784.5 | False | 51.3/6025.4 |
| rilde_in_elder | 4/4 | 754.2〜770.1 | False | 51.3/6006.2 |
| rilde_in_house_01 | 4/4 | 752.6〜770.3 | False | 51.3/6088.3 |
| rilde_in_house_02 | 4/4 | 755.3〜764.7 | False | 51.3/6068.4 |
| rilde_in_house_03 | 4/4 | 753.9〜761.7 | False | 51.3/6088.3 |
| rilde_in_house_04 | 4/4 | 754.7〜763.8 | False | 51.3/6081.3 |
| rilde_in_inn_1f | 4/4 | 757.1〜768.4 | False | 51.3/5922.5 |
| rilde_in_inn_2f | 4/4 | 753.5〜762.0 | False | 51.3/6223.7 |
| rilde_in_shop | 4/4 | 754.3〜763.1 | False | 51.3/6006.2 |
| rilde_in_storage | 4/4 | 753.1〜760.9 | False | 51.3/6130.9 |
| rilde_village_01_peace | 4/4 | 786.6〜913.1 | False | 51.3/5905.9 |
| rilde_village_01_ruin | 4/4 | 797.9〜871.5 | False | 51.3/123.0 |
| road_dunvall_capital_01 | 4/4 | 777.8〜847.4 | False | 51.3/1578.9 |
| royal_capital_00_gate | 4/4 | 767.4〜789.8 | False | 51.3/1180.0 |
| royal_capital_01_market | 4/4 | 767.0〜780.5 | False | 51.3/2357.2 |
| royal_capital_02_castle_plaza | 4/4 | 769.0〜774.4 | False | 51.3/496.6 |
| royal_capital_03_residential | 4/4 | 764.9〜772.7 | False | 51.3/2630.3 |
| royal_in_guild | 4/4 | 758.5〜773.5 | False | 51.3/730.6 |
| royal_in_inn | 4/4 | 754.1〜758.9 | False | 51.3/157.9 |

120条件でdefault spawnは自由、表示中の追従は300px以内、屋内のLou非表示・join gate・昼夜を確認した。Fiona/Louの非表示時の距離はUI不具合として数えない。

## 遷移先JSON不存在

| map / exit | toMap | enabled | 原因分類/扱い |
|---|---|---|---|
| cliff_moher_01_spiral_ascent / tr_c1_to_lind | lind_village | True | hook-owned legacy |
| fort_dunvall_01_courtyard / tr_f1_to_village | lind_village | True | hook-owned legacy |
| moss_forest_01_sunlit_path / tr_to_lind | lind_village | True | hook-owned legacy |
| moss_forest_03_ancient_grove / tr_to_deep | TBD | False | TBD |
| rilde_village_01_peace / tr_v_to_cliff | TBD | True | TBD |
| rilde_village_01_peace / tr_v_to_fort | TBD | True | TBD |
| rilde_village_01_ruin / tr_v_to_cliff | TBD | True | TBD |
| rilde_village_01_ruin / tr_v_to_fort | TBD | True | TBD |
| royal_capital_01_market / tr_r1_to_craft | TBD | True | TBD |
| royal_capital_02_castle_plaza / tr_r2_to_east | TBD | True | TBD |
| royal_capital_02_castle_plaza / tr_r2_castle_gate | TBD | True | TBD |

rilde_villageはRildeVillage.resolveでpeace/ruinへ解決して実在するため未解決にしない。lind_villageは旧DOM/遷移hookが受け持ち、JSONが無いことだけでは遷移不能を意味しない。TBDの一部（村の断崖/砦）はhookで受ける場合があり、受け口未接続の王都3出口と同じ原因にまとめない。moss tr_to_deepはdisabledである。

分類: 動的エラー0。不存在はデータのTBD/旧virtual/hook形式で、コード回帰を再現したものではない。次の提案はhookの受け口を明示した遷移検証、王都受け側JSONが確定してから接続。マップを勝手に作らない。

[全結果/イベント/ログ](all-maps-smoke-20261013/) を保存。再実行 `python tests/moss/m35_all_maps_smoke.py`、自身の8834 server終了。Android実機・全named spawnの歩行到達・NPC台詞/全敵AI・全回帰は未実施。次PP。main未統合、将来の戻し方git revert -m 1 <merge>。
