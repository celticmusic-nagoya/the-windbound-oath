# 天候・木漏れ日・町の歩行 (M9)

## FieldWeather (`js/field/field-weather.js`)
画面オーバーレイ `#forestWeather`（z55、時間帯グレード `#forestTod` の直下）に **霧2層 + もや + 雨パーティクル(canvas)** を描く。セーブしない（マップデータ＋ストーリー状態から毎回導出）。

マップJSON（任意）:
```json
"weather": {"default": "fog",
  "rules": [{"when": {"sealOpen": true}, "set": "mist", "ms": 6000},
            {"when": {"stage": [12, null]}, "set": "clear", "ms": 9000}]}
```
- `when` は TalkConditions 条件（flag / stage / sealOpen / quest / item …）。**最後に成立した rule が勝ち**、無ければ `default`。`weather` 無しのマップは `clear`。
- 約1秒ごとに再評価。変化すると `ms`（既定5000）かけて霧/雨が増減する。イベント `field-weather` が飛ぶ。
- プリセット: `clear` / `mist` / `fog`(濃霧) / `rain` / `storm`。`FieldWeather.set(name,{ms,instant})` は手動（次のマップ切替まで）。
- 霧・雨は `FieldTimeOfDay.setOcclusion()` で日差しを遮る → **霧が晴れると光の筋・木漏れ日が戻る**。
- `prefers-reduced-motion` では雨粒を出さず、霧は静止。

| マップ | default | 変化 |
|---|---|---|
| moss_forest_01 / 03 | fog | 封印解放(異形3体撃破)→ mist、ライダー撃破(stage12+)→ clear |
| moss_forest_02 | rain | 同上 |
| fort_dunvall_02_ramparts | mist | — |
| royal_capital_03_residential | rain | q_capital_comb 完了/報告済み → clear |

## FieldTimeOfDay キャノピー層
マップに `"timeOfDay":{"default":"day","canopy":true}`（または `{beams,dapple,leaves,moss}` 各0..1）。プリセット(day/dusk/night)ごとに不透明度と光色が変わる。
- `beams` 光の筋 / `dapple` 木漏れ日（ゆっくり流れ呼吸する光斑）/ `leaves` 葉揺れ（2層・位相違い）/ `moss` 画面端の苔の斑。
- テクスチャは全て JS で生成（画像ファイル無し）。canopy 未指定のマップでは非表示。

## FieldWalkers（町NPCの6フレ歩行）
マップJSON `"walkers":[{id,look,x,y,path:[[dx,dy]..],speed,rest}]`。`look` は `npc_slot_<look>` のマニフェスト規則（`walk:{file,frames:6}`）。
静的propの代わりに描画し、プレイヤーが56px以内に居る間は立ち止まる。素材は `tools/moss/make_npcs.py` が `npc_<look>_walk_01..06.png`（1ドット=2px・足元中央・透過PNG）を出力。
`tools/moss/build_town_maps.py` の `m.npc(..., walk=[[dx,dy],..])` で指定。通行不可地点は tests/moss/m9_env.py が検出する。

## リルド村
- 商人 `merchant_walk_01..06`: 既存イラストから `tools/lind/make_walk_from_idle.py`（変位ワープ）で生成 → `install_walk_frames.py --write-bounds`。
- 少年剣士（モブ・訓練場）: `tools/lind/make_swordboy.py` が `boy_swordsman_idle` + `boy_swordsman_attack_01..06`（木剣素振り）を生成。`LindSwordBoy` が待機⇄素振りをループ。主人公の戦闘モーション(battle manifest)とは無関係。

テスト: `python3 tests/moss/m9_env.py`
