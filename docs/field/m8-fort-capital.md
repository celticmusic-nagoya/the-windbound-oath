# ドゥンヴァル砦・王都 基礎マップ / 装備拡充

## マップ（`python3 tools/moss/build_town_maps.py` で `data/maps/*.json` を生成・到達性検証）
- 砦: `fort_dunvall_01_courtyard`（外門・城壁・四隅の見張り塔・主塔・兵舎/厩）→ `_02_ramparts`（城壁の歩廊・見張り台）/ `_03_keep`（大広間）。
- 王都: `royal_capital_01_market`（商業区）/ `_02_castle_plaza`（城前広場・城門・噴水）/ `_03_residential`（住宅街・家10軒の扉ノード）。
- 構成方針: **エリアごとに1マップ（シーン）＋トランジション接続**。1枚の巨大マップにしない理由 = カリング/コリジョン生成/フェードの単位が小さく保てる、エリア毎にBGM・時間帯・ロード対象を切替えられる、将来のNPC・イベントが各マップのJSONで独立管理できる、モバイルのメモリ上限に優しい。ゲーム中はキャッシュ済みマップの再入場が速い。
- NPC/ショップ/依頼人の枠 = `eventZones` の `interact`（`eventId:"npc_<id>"`, `role: shop|quest|npc`, `placeholder:true`）。家の扉は `door_house_NN`。宝箱の枠は `treasurePoints`（`tr_f*/tr_r*`）。中身は未設定（`ItemData.treasure` に足すだけ）。
- ワールド接続が未実装の出口は `toMap:"TBD"`（通ると「この先は、まだ道が続いていない」）。扉の矩形は必ず外周ブロッカーの内側に置く（ツールが検証）。
- 確認用入口: `enterWorldMap('fort'|'capital')`（物語には未接続）。テスト: `tests/moss/m8_town_maps.py`。見た目は塗り矩形＋仮ノードのみ。

## 装備・ショップ
- 追加装備: 革の帽子(頭 DEF+1)・布のチュニック(胴 DEF+1)・革の鎧(胴 DEF+3)・銅の指輪(装飾 MaxHP+5)。
- ショップ: `js/data/shop-data.js`（`ShopData`）＋ `js/shop.js`（購入ロジック＋モーダル）。道具屋の会話の選択肢「買い物をする」から開く（talk効果 `{shop:id}`）。**stage 15 になるまで営業しない**（プロローグ/Raiderのバランス不変）。
- 売価案: 革の帽子 60G / 布のチュニック 50G / 銅の指輪 90G / 革の鎧 220G（きずぐすり 20G・魔力の雫 45G）。
- 宝箱: `tr_a1_wayside_late`(銅の指輪)・`tr_a2_ledge_late`(革の鎧) を追加。`ItemData.treasureStage` により stage 15 まで開かない。
- テスト: `tests/system/shop_flow_test.py`

## ストーリー接続（仮シナリオ）
- 村の東の看板 `#roadExit` →（stage≥15 かつ長老の話で `road_dunvall_open`）→ 砦の中庭。砦の南門＝村へ戻る／東門＝王都の西門。王都の西門＝砦へ。王城の門だけ未接続(TBD)。
- NPC/ショップ/ベッド/掲示板は map の click-only ノード（`npc` / `shop` / `action:'rest'`）。会話表 `js/field/talk-data-capital.js`（全て仮の台詞）。
- 休息: 兵舎の仮眠所。現状HP/MPは戦闘ごとに全回復で持ち越し状態が無いので、演出＋`party-rest` イベントのみ（永続HPを入れる時にここへ繋ぐ）。
- サブクエスト: 「王都の失くし物」(住宅街の老婦人 → 城前広場の花壇の箱の銀の櫛 → 80G+魔力の雫) / 「商業区の納品依頼」(掲示板 → きずぐすり3つ → 90G+魔力の雫、達成で武具店に鋼の剣が並ぶ)。
- ショップ: `dunvall_arms` / `royal_general` / `royal_arms`（王都限定: 騎士の兜・鎖帷子・銀の指輪・鋼の剣）。`stock[].quest|flag|minStage` で品揃えを条件付けできる。
- テスト: `tests/system/capital_story_test.py`

## 自動生成アセット（差し替え前提の仮絵）
- `tools/moss/make_props.py`: 柵(杭/壊れ柵)・ベンチ・標識(2種)・立石・境界石を 2world px=1ドット のドット絵で生成し manifest の `node` 先頭に登録（`gen:make_props`、再実行は冪等）。
- `tools/moss/make_npcs.py`: 兵士/隊長/門番/商人/町人(男女)/老人/子ども/吟遊詩人/依頼人 + ベッド + 掲示板（2.5頭身・前向き1枚絵）。`npc_slot_<look>` として登録。
- 石畳・レンガ・屋根瓦・板張りは `terrain.fills[].pattern`（`flagstone|brick|planks|roof|cobble`）で手続き描画（画像不要）。
- 崖マップに立石の当たり判定プリセットを追加。`check_assets.py` は全マップを対象に art/collision 幅を検査（現在 警告0）。
