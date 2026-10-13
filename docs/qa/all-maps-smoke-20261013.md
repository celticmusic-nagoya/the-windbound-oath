# OO 全30フィールドマップ巡回スモーク

初回mainf0fe968 / 追試maindeadf3d（source f9136bf） / work/codex-ll-pp。m35_all_maps_smoke.pyと本報告/JSON/ログのみ、マップ/ゲームは未編集。

30map×Lou合流有無×昼夜=120条件完了。動的case合格120 / 失敗0 / 未実施0、pageerror/console event 0。遷移先JSONの存在確認は未解決11件（TBD8、hook-owned lind_village3）。FAILS11/exit1を保持。これを11個の新規ランタイム破損と同一視しない。

## マップ別

読み込み時間はMossForest.enterの完了までのwall clock、同一browserのcacheを共有。ネットワーク実機時間ではない。初期の明るさ/暗さ設定は即時、AIは凍結して戦闘に入らないスモーク。高さoverlayは本編既定OFF、inline DEV高度は通常loaderのまま。デフォルトspawnのみで、全spawnや出口を実際に歩いた試験ではない。

| map | 合格条件/4 | load min〜max ms | default blocked | 最大Fiona/Lou距離px |
|---|---:|---:|---|---:|
| cliff_moher_01_spiral_ascent | 4/4 | 931.8〜954.6 | False | 51.3/nan |
| dev_height_proto | 4/4 | 759.9〜787.4 | False | 16.0/2465.9 |
| dev_monster_arena | 4/4 | 757.1〜764.4 | False | 51.3/2186.3 |
| fort_dunvall_01_courtyard | 4/4 | 770.0〜802.3 | False | 51.3/1704.9 |
| fort_dunvall_02_ramparts | 4/4 | 767.0〜781.0 | False | 51.3/375.9 |
| fort_dunvall_03_keep | 4/4 | 760.2〜774.1 | False | 51.3/1157.9 |
| fort_in_tavern | 4/4 | 759.3〜774.1 | False | 51.3/723.9 |
| moss_forest_01_sunlit_path | 4/4 | 826.8〜867.1 | False | 51.3/4873.4 |
| moss_forest_02_mossy_ravine | 4/4 | 863.5〜897.1 | False | 51.3/7180.8 |
| moss_forest_03_ancient_grove | 4/4 | 836.3〜890.5 | False | 51.3/7455.1 |
| rilde_in_aidan | 4/4 | 754.3〜755.6 | False | 51.3/6221.3 |
| rilde_in_barn | 4/4 | 752.3〜771.6 | False | 51.3/6025.4 |
| rilde_in_elder | 4/4 | 754.8〜764.5 | False | 51.3/6006.2 |
| rilde_in_house_01 | 4/4 | 756.7〜766.9 | False | 51.3/6088.3 |
| rilde_in_house_02 | 4/4 | 755.0〜770.5 | False | 51.3/6068.4 |
| rilde_in_house_03 | 4/4 | 755.1〜762.9 | False | 51.3/6088.3 |
| rilde_in_house_04 | 4/4 | 752.6〜763.9 | False | 51.3/6081.3 |
| rilde_in_inn_1f | 4/4 | 757.0〜775.1 | False | 51.3/5922.5 |
| rilde_in_inn_2f | 4/4 | 752.8〜762.8 | False | 51.3/6223.7 |
| rilde_in_shop | 4/4 | 755.0〜766.7 | False | 51.3/6006.2 |
| rilde_in_storage | 4/4 | 753.5〜760.0 | False | 51.3/6130.9 |
| rilde_village_01_peace | 4/4 | 781.6〜914.2 | False | 51.3/5905.9 |
| rilde_village_01_ruin | 4/4 | 790.9〜858.8 | False | 51.3/123.0 |
| road_dunvall_capital_01 | 4/4 | 778.0〜820.4 | False | 51.3/1578.9 |
| royal_capital_00_gate | 4/4 | 766.5〜786.5 | False | 51.3/1180.0 |
| royal_capital_01_market | 4/4 | 770.6〜776.0 | False | 51.3/2357.2 |
| royal_capital_02_castle_plaza | 4/4 | 768.3〜777.2 | False | 51.3/496.6 |
| royal_capital_03_residential | 4/4 | 764.9〜769.9 | False | 51.3/2630.3 |
| royal_in_guild | 4/4 | 760.8〜772.0 | False | 51.3/730.6 |
| royal_in_inn | 4/4 | 753.5〜761.1 | False | 51.3/157.9 |

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

最新field描画でも120条件全合格/エラー0、遷移JSON未解決11は同じ。表/JSON/logを追試へ更新。
