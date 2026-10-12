# 全マップ調査 (2026-10-13)

基準コード: `03d053e` / 調査HEAD `66b2828cfb890c8a7fc258864b7a8a4e67d3d3c8`。マップ **29件**。ブランチ `work/codex-night-j`。STATUS: READY（静的調査）。mainへの反映なし。

件数はJSONに明示されたもの。NPCは描画用npc_ asset/npcタグのprops数＋walkers数（ベッド等のNPC slot代用を含む、会話refの数は足さない）。敵はmonsters/enemies定義数＋story.prologue.symbols数、遭遇ゾーンは別記。宝箱欄はtreasurePoints総数（採取ポイントも含み、JSONのherbsで別集計）。runtimeが生成するスライム等の実在数は含まない。地形はterrain直下の配列要素の合計、オブジェクトはprops数。屋内はstory.interiorまたは命名からの推定。

到達は既存mf_lib.Hashの22×10足元とforest-loaderのrect/preset方式を参照した独立2D静的チェック。default spawnから32px四近傍、各辺を8px以下でサンプル。spawnは正確な地点、遷移はrect内、宝箱は100px以内への接近。条件付きblockerは全flag false/trueを分ける。散布node衝突、動くNPC、ストーリー条件、イベント発火と高さは再現しない。「未到達」は細い通路/格子/条件の問題を含む調査候補。ゲームの到達可否の断定ではない。

| マップID / 表示名 | サイズ | 地形/props | NPC props+歩行 | 明示敵+story / 遭遇zone(有効) | 宝箱 / event / 遷移(有効) | height / 屋内外 | 到達サンプル | 立体化候補 / 必要素材（推定） |
|---|---|---|---|---|---|---|---|---|
| cliff_moher_01_spiral_ascent / 風見の断崖 | 4800×4800 | 20/244 | 0+0 | 0+0 / 0(0) | 5/4/1(1) | なし / 屋外推定 | 8/8 | 崖/高台 / 崖正面・上端・角 |
| fort_dunvall_01_courtyard / ドゥンヴァル砦　中庭 | 3200×2400 | 6/67 | 3+1 | 0+0 / 0(0) | 1/5/5(5) | なし / 屋外推定 | 11/11 | 階段/坂・城壁/主塔（IDからの候補） / 階段/坂4方向・踊り場・石壁側面・階段・欄干 |
| fort_dunvall_02_ramparts / ドゥンヴァル砦　城壁 | 2800×1600 | 3/36 | 0+1 | 0+0 / 0(0) | 1/2/2(2) | なし / 屋外推定 | 5/5 | 階段/坂・城壁/主塔（IDからの候補） / 階段/坂4方向・踊り場・石壁側面・階段・欄干 |
| fort_dunvall_03_keep / ドゥンヴァル砦　主塔 | 2400×1800 | 5/20 | 2+0 | 0+0 / 0(0) | 1/3/2(2) | なし / 屋内推定 | 5/5 | 階段/坂・城壁/主塔（IDからの候補） / 階段/坂4方向・踊り場・石壁側面・階段・欄干 |
| fort_in_tavern / ドゥンヴァル砦　酒場「錆びた角笛」 | 1400×1000 | 4/34 | 6+0 | 0+0 / 0(0) | 0/7/1(1) | なし / 屋内推定 | 2/2 | 城壁/主塔（IDからの候補） / 石壁側面・階段・欄干 |
| moss_forest_01_sunlit_path / 陽だまりの森道 | 9600×6000 | 14/40 | 0+0 | 18+0 / 6(6) | 5/7/2(2) | なし / 屋外推定 | 10/10 | 明示的な候補なし / 候補決定後 |
| moss_forest_02_mossy_ravine / 苔むした渓谷 | 9600×7200 | 17/25 | 0+0 | 24+0 / 7(0) | 5/6/2(2) | なし / 屋外推定 | 9/9 | 崖/高台・階段/坂・橋/桟橋・滝/低地・樹冠 / 崖正面・上端・角・階段/坂4方向・踊り場・床・側面・欄干・橋脚・滝・水際・低地の縁・上層樹冠・通行用根アーチ |
| moss_forest_03_ancient_grove / 古樹の聖域 | 8400×6600 | 12/151 | 0+0 | 9+3 / 8(1) | 4/8/2(1) | なし / 屋外推定 | 5/8 / 7/8 | 崖/高台・樹冠 / 崖正面・上端・角・上層樹冠・通行用根アーチ |
| rilde_in_aidan / エイダンの家 | 960×720 | 4/17 | 0+0 | 0+0 / 0(0) | 0/7/1(1) | なし / 屋内推定 | 4/4 | 明示的な候補なし / 候補決定後 |
| rilde_in_barn / 納屋 | 1000×700 | 4/15 | 0+0 | 0+0 / 0(0) | 0/4/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_elder / 長老の家 ― 風見の丘 | 960×720 | 4/17 | 1+0 | 0+0 / 0(0) | 0/8/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_house_01 / 村人の家 | 860×640 | 4/13 | 0+0 | 0+0 / 0(0) | 0/6/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_house_02 / 村人の家 | 860×640 | 4/16 | 0+0 | 0+0 / 0(0) | 0/6/1(1) | なし / 屋内推定 | default_spawn_blocked | 明示的な候補なし / 候補決定後 |
| rilde_in_house_03 / 村人の家 | 860×640 | 4/14 | 0+0 | 0+0 / 0(0) | 0/5/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_house_04 / 村人の家 | 860×640 | 4/14 | 0+0 | 0+0 / 0(0) | 0/5/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_inn_1f / 宿屋「風見鶏」 1階 | 1200×800 | 4/26 | 2+0 | 0+0 / 0(0) | 0/5/2(2) | なし / 屋内推定 | 5/5 | 階段/坂 / 階段/坂4方向・踊り場 |
| rilde_in_inn_2f / 宿屋「風見鶏」 2階 | 1100×760 | 4/12 | 0+0 | 0+0 / 0(0) | 0/7/1(1) | なし / 屋内推定 | 3/3 | 階段/坂 / 階段/坂4方向・踊り場 |
| rilde_in_shop / 道具屋「若葉の袋」 | 960×720 | 4/15 | 1+0 | 0+0 / 0(0) | 0/5/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_in_storage / 倉庫 | 760×600 | 4/10 | 0+0 | 0+0 / 0(0) | 0/5/1(1) | なし / 屋内推定 | 3/3 | 明示的な候補なし / 候補決定後 |
| rilde_village_01_peace / リルド村 | 2400×1750 | 16/115 | 6+10 | 0+0 / 0(0) | 0/26/12(12) | なし / 屋外推定 | 28/28 | 崖/高台・橋/桟橋 / 崖正面・上端・角・床・側面・欄干・橋脚 |
| rilde_village_01_ruin / リルド村（襲撃後） | 2400×1750 | 25/164 | 7+0 | 0+0 / 0(0) | 0/23/2(2) | なし / 屋外推定 | 18/18 | 崖/高台・橋/桟橋 / 崖正面・上端・角・床・側面・欄干・橋脚 |
| dev_monster_arena / DEV　モンスター配置アリーナ | 4800×3200 | 0/0 | 0+0 | 0+0 / 0(0) | 0/1/0(0) | なし / 屋外推定 | 1/1 | 明示的な候補なし / 候補決定後 |
| road_dunvall_capital_01 / 街道　砦と王都のあいだ | 5600×2600 | 4/268 | 2+1 | 6+0 / 0(0) | 0/6/2(2) | なし / 屋外推定 | 5/5 | 明示的な候補なし / 候補決定後 |
| royal_capital_00_gate / 王都カエルディン　南大城門・旅人街 | 4400×3400 | 5/68 | 1+3 | 0+0 / 0(0) | 1/5/4(4) | なし / 屋外推定 | 10/10 | 明示的な候補なし / 候補決定後 |
| royal_capital_01_market / 王都　商業区 | 4800×3200 | 2/57 | 2+2 | 0+0 / 0(0) | 1/5/4(4) | なし / 屋外推定 | 9/9 | 明示的な候補なし / 候補決定後 |
| royal_capital_02_castle_plaza / 王都　城前広場 | 4000×3600 | 3/49 | 1+2 | 0+0 / 0(0) | 1/4/4(4) | なし / 屋外推定 | 9/9 | 明示的な候補なし / 候補決定後 |
| royal_capital_03_residential / 王都　住宅街 | 3600×3200 | 2/32 | 1+2 | 0+0 / 0(0) | 1/14/2(2) | なし / 屋外推定 | 5/5 | 明示的な候補なし / 候補決定後 |
| royal_in_guild / 冒険者ギルド兼大酒場 | 1800×1100 | 4/30 | 6+0 | 0+0 / 0(0) | 0/8/1(1) | なし / 屋内推定 | 2/2 | 明示的な候補なし / 候補決定後 |
| royal_in_inn / 宿屋「旅人の灯」 | 1400×1000 | 4/14 | 3+0 | 0+0 / 0(0) | 0/4/1(1) | なし / 屋内推定 | 2/2 | 明示的な候補なし / 候補決定後 |

## 未到達の調査候補（flags別）

- `moss_forest_03_ancient_grove` flags={'moss_a3_seal_open': False}: spawn:dev_sanctuary, treasure_approach:tr_a3_hollowlog, transition:tr_to_deep
- `moss_forest_03_ancient_grove` flags={'moss_a3_seal_open': True}: transition:tr_to_deep
- `rilde_in_house_02` flags={}: default_spawn_blocked

## JSON未解決接続 / spawn不一致

未解決は欠損と確定しない。lind_village等はruntime hookで処理される場合がある。無効/TBDもそのまま列挙。
- `cliff_moher_01_spiral_ascent` / `tr_c1_to_lind` → `lind_village` / `from_cliff`: external_hook_or_missing、enabled=True
- `fort_dunvall_01_courtyard` / `tr_f1_to_village` → `lind_village` / `from_fort`: external_hook_or_missing、enabled=True
- `moss_forest_01_sunlit_path` / `tr_to_lind` → `lind_village` / `from_moss_forest`: external_hook_or_missing、enabled=True
- `moss_forest_03_ancient_grove` / `tr_to_deep` → `TBD` / `TBD`: external_hook_or_missing、enabled=False
- `rilde_in_aidan` / `tr_exit` → `rilde_village` / `from_aidan`: external_hook_or_missing、enabled=True
- `rilde_in_barn` / `tr_exit` → `rilde_village` / `from_barn`: external_hook_or_missing、enabled=True
- `rilde_in_elder` / `tr_exit` → `rilde_village` / `from_elder`: external_hook_or_missing、enabled=True
- `rilde_in_house_01` / `tr_exit` → `rilde_village` / `from_house_01`: external_hook_or_missing、enabled=True
- `rilde_in_house_02` / `tr_exit` → `rilde_village` / `from_house_02`: external_hook_or_missing、enabled=True
- `rilde_in_house_03` / `tr_exit` → `rilde_village` / `from_house_03`: external_hook_or_missing、enabled=True
- `rilde_in_house_04` / `tr_exit` → `rilde_village` / `from_house_04`: external_hook_or_missing、enabled=True
- `rilde_in_inn_1f` / `tr_exit` → `rilde_village` / `from_inn`: external_hook_or_missing、enabled=True
- `rilde_in_shop` / `tr_exit` → `rilde_village` / `from_shop`: external_hook_or_missing、enabled=True
- `rilde_in_storage` / `tr_exit` → `rilde_village` / `from_storage`: external_hook_or_missing、enabled=True
- `rilde_village_01_peace` / `tr_v_to_cliff` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `rilde_village_01_peace` / `tr_v_to_fort` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `rilde_village_01_ruin` / `tr_v_to_cliff` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `rilde_village_01_ruin` / `tr_v_to_fort` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `royal_capital_01_market` / `tr_r1_to_craft` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `royal_capital_02_castle_plaza` / `tr_r2_to_east` → `TBD` / `TBD`: external_hook_or_missing、enabled=True
- `royal_capital_02_castle_plaza` / `tr_r2_castle_gate` → `TBD` / `TBD`: external_hook_or_missing、enabled=True

## 再実行 / 未検証

```sh
python3 tools/moss/survey_maps.py > docs/qa/map-survey-20261013.md
python3 tools/moss/survey_maps.py --json > docs/qa/map-survey-20261013.json
```

JSONは各マップのSHA256、地形カテゴリ別個数、NPC ID、接続、到達ターゲット/flagsを保持する。上の標準実行とJSON実行は同じsurvey関数を使う。チェッカーcheck_a2はA2設計専用のルート・座標を要求するため全件に流用せず、Hashだけ再使用し実JSONのcollision.presetsを読む。

立体化候補はID/地形/props/遷移noteからの推定で、必要な段差・高さ・新マップを確定しない。採用済み画像/JSONは未編集。橋の上下通行や屋根/樹冠遮蔽は高さ実装と作者確認が必要。Android負荷、全マップ歩行、宝箱の実開封、ストーリー全ゲートは未検証。資料/新規ツールだけなのでmainのロールバック不要。
