# DIRECTIVE-ART-04 — 室内・王国兵士の高精細リニューアル（04A仕様／04B自宅試作／04C兵士試作）

- 基準: main `312bfb4`（DIRECTIVE-26B反映後）へrebaseした `art/art-01-early-maps`（Draft PR #101）。**04D（横展開）は未着手。ユーザー視覚承認待ち**。
- 変更なし: ゲームコード・map・manifest・正式採用台帳・既存PNG（正式259 SHA 259/259一致）。ART-01の室内候補10件は比較用に保持。新素材は `docs/art/candidates/art-04/` に隔離。
- **コンセプト画像について**: 本指示にある「承認済みコンセプト画像」はこのセッションに添付されておらず参照できていない。今回は指示どおり、既存の屋外マップ（`rilde/lind/lind_aidan_house.png` 等）・エイダン・村人NPCを正本として制作した。コンセプト画像を添付いただければ、色調と意匠を照合して修正する。
- 画像生成AIはこのセッションで使えないため、全素材を `tools/art/` のスクリプトでドット単位に描画している（決定的出力）。

## ART-04A 仕様・比較

### 既存の描画仕様（実測）

| 対象 | 方式 | サイズ・anchor |
|---|---|---|
| 屋外の正式建物 | 絵画調ドット、world 1px＝原画2px（例 `lind_aidan_house` 580×466 → w290 h233） | 下中央 |
| 室内家具54PNG | 4×4pxブロック・色数4〜13の平塗り（`gen: rilde`）。manifest w/h で原画の1/2表示 | 下中央 |
| 室内の床・壁 | 画像なし。単色fill＋手続き線（`forest-layer.js`） | map矩形 |
| 村人NPC | 絵画調（元520×420 → 縮小 例92×114、w63 h78）、半透明の縁あり | 下中央 |
| 兵士・隊長・衛兵 | 4pxブロック・18色の簡易ドット、`npc_slot_*` w56 h84（原画112×168）。field-walkersが **idle＋正面歩行6コマ** を使い、左右は`scaleX(-1)`で反転 | 下中央（足元） |
| エイダンfield | 2048×1280 キャンバス、scale 0.0625、可視高 約69 world | 足元anchor |

→ 新素材は **world 1px＝2px（@2x）・既存と同じ w/h・下中央anchor** で作る。αは0/255のみ（完全透過、半透明なし）。

### 家具54PNGの分類

| 分類 | 件数 | 内容 |
|---|---|---|
| 再利用（今回は変更しない） | 13 | 未使用5（burnt_beam, counter, rubble_l, spill_bowl, window_light）、屋外専用8（廃墟の ash_patch, banner_torn, cart_wreck, post_burnt, rubble_m, rubble_s, scorch、平和村の cat_white） |
| 再制作（同じfootprintで高精細化） | 41 | 室内で使う家具・小物すべて（bed, bed_small, bench, chair, chair_back, counter_inn, counter_shop, cupboard, fireplace, shelf_books/goods/pots, table_long/round/small, stool, window_wall, door_wall, tapestry, rug_green/red, doormat, barrel, basket, bucket, jar, crate, crates_stack, sack, sacks_pile, plant_pot, candle_stand, spinning_wheel, tool_rack, weapon_rack, map_table, herb_bundle, hay_bale, stairs_up/down, rune_pillar）。barrel・crate類は王都・砦の屋外でも共用 |
| 追加（新規の室内専用素材） | 10 | 床・壁（梁/漆喰/腰壁）・巾木・外壁天端（左/右/手前）・角（南西/南東）・扉枠と敷居（以上9件はART-04Bで試作済み）、窓の光だまり（未制作） |

### 兵士の制作対象（現行field仕様から決定）

field-walkersは正面idle＋正面歩行6コマ＋左右反転だけを使う。背面・側面のコマは現行コードでは表示されないため、**正面idle 1＋正面歩行6 ＝ 1系統7枚**を制作単位とする（背面・左右が必要ならCodex側の描画対応が先）。3系統（一般兵士・隊長・衛兵）で計21枚。既存設定（兜と赤い房、青い上衣と金の帯、槍、赤い盾／隊長は赤衣と金の房、衛兵は盾なし）は維持し、新装備は加えない。

## ART-04B 自宅の試作（13件、うち4件は家具の再制作）

| ファイル | world | 役割 |
|---|---|---|
| `art04_int_floor_planks_01.png` | 112×112 | 床。板幅28（現行と同じ）、木目の筋、継ぎ目は板1枚につき1か所、釘はART-01の半分 |
| `art04_int_wall_timber_01.png` | 224×150 | 奥壁。天井梁・漆喰パネル・柱・筋交い・中桟・腰壁・笠木。外観のハーフティンバーと揃えた |
| `art04_int_baseboard_01.png` | 112×12 | 巾木 |
| `art04_int_wallcap_left/right/bottom_01.png`、`corner_sw/se_01.png` | 48幅 | 外壁の天端（濃い木口と、室内側の明るい縁） |
| `art04_int_doorway_01.png` | 140×48 | 厚みのある扉枠・鉄の蝶番・石の敷居・外光。`tr_exit`（x410〜550）と同幅 |
| `art04_furn_window_wall_01.png` | 64×76 | 窓。木枠・十字の桟・空のグラデーション・映り込み・窓台 |
| `art04_furn_fireplace_01.png` | 152×136 | 暖炉。不揃いの石積み・アーチ・薪・3層の炎・自在鉤・木のマントル |
| `art04_furn_bed_01.png` | 124×92 | ベッド。彫りのある頭板、ケルト風の組紐帯、枕、緑のキルト |
| `art04_furn_cupboard_01.png` | 92×116 | タンス。鏡板の扉2枚・真鍮の取っ手・組紐の紋。**調べる位置・当たり判定は不変**（同じfootprint） |

比較: `compare_house_art04.png`（PC／Android横相当／縦相当 × 現在・ART-01・ART-04）、`compare_house_art04_detail.png`（暖炉・ベッド/タンス/窓・入口の2倍拡大）。どちらも実ゲームの描画経路でブラウザ内だけ差し替えて撮影（Codex K1/K2の試作を兼ねる）。

自己評価: 床・壁・扉・4家具は、屋外の木と漆喰の色調・密度にかなり近づいた。本棚・タペストリー・絨毯・テーブル・椅子・小物は旧素材のままなので、同じ画面で平板さが目立つ（04Dの対象）。床は横表示でも継ぎ目の反復は目立たない。

## ART-04C 一般兵士の試作

`art04_npc_soldier_front_idle_01.png`（112×168、world 56×84、足元y=165で下中央anchor。現行slotと同じ）。

比較: `compare_soldier_art04.png`（平和村／襲撃後の北側 × PC／Android縦相当。左から老人・旧兵士・新兵士・若い女性、近くにエイダン）、`compare_soldier_scale.png`（同一world縮尺の並び）。

自己評価: 旧兵士より、輪郭・陰影・顔（大きな目とハイライト）・兜の鋲・盾の真鍮の縁などで村人にかなり近づいた。ただし村人は絵画調の筆致（布のしわ、髪の流れ）が細かく、新兵士は面がまだ均一でクリーン寄り。全高は村人（78）より少し高い（84、現行slot規格どおり）。スマホ縦表示でも兜・槍・盾は判別できる。

## 04Dへ進む前に決めていただくこと

1. 自宅の方向性（漆喰＋梁の壁、明るい板床）で残り37家具と他13室内へ進めてよいか
2. 一般兵士の品質（顔の描き方・頭身）をこの方向で確定し、歩行6コマ→隊長・衛兵へ進めてよいか
3. コンセプト画像の再添付（照合用）

再現: `python3 tools/art/make_art04_interior.py && python3 tools/art/make_art04_soldier.py`。比較画像は `python3 -m http.server 8765` を起動したうえで `cd tools/art && python3 preview_art04.py`（生の撮影画像 `preview/` はコミットしない）。
