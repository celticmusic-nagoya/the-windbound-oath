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
