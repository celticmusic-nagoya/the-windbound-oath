# FIELD-VISUAL-OVERHAUL-02 / Phase 1 — 現行フィールド実装監査
調査日: 2026-11-08 / 範囲: main のソース・パスと登録仕様の静的確認。画像実機表示・全PNG SHAの再計算は未実施。

## 監査の要約
- リポジトリの `img/field/` 配下に PNG **760件**（Git tree一覧で集計）。**正式採用760件という意味ではない**。候補・DEV・素材を含むため採用台帳照合が必要。
- `js/field/` 配下の JS **65件**。複数のフィールド描画経路（プレイヤー、NPC walker、敵、Lind DEV）が存在する。単一描画ループへの無検証置換は避ける。
- 現行マップは `data/maps/` 配下にリルド村（平和/廃墟）、モスの森、砦、王都、屋内などのJSON。クォータービューへの移行は地形表示だけでなく、座標、遮蔽、接地、通路、イベント、SAVEとの整合が必要。

## 描画経路と変更影響
| 対象 | 現行実装 | 観測した仕様 | 新方式への移行ゲート |
|---|---|---|---|
| エイダンPC（DEV描画） | `js/field/aidan-field-assets.js`, `aidan-field-actor.js`, `aidan-heading.js` | 2048×1280の方向別PNG、anchor例[1024,1230]、scale 0.0625。現行WALKは複数フレームを100msごとに切替。画像描画は既存位置へ重ね、衝突は別。 | 新静止スプライトの各方向/接地点/見た目のバウンスを既存位置・判定と分離。DEV試験から開始 |
| NPC walker | `js/field/field-walkers.js` | manifestの `npc_slot_*` ルールから6コマを参照、足元座標で移動。待機・接近停止・ルート移動。 | 方向別静止画へ段階置換。移動・接近停止・zIndex(y)維持 |
| フィールド敵 | `js/field/field-monsters.js` | `MONSTER_TYPES`にモススライム6コマ、フォレストバット4、リーフィボア11、ゴブリン等。単一update、距離/当たり判定は足元で評価。 | アニメーションを見た目だけに適用。警戒/追跡/接触/戦闘状態を維持 |
| ルー | `img/field/characters/lou/` | PNG6件を確認。 | 妖精固有サイズと浮遊・光粒子を個別設計 |
| リルドNPC/建物 | `js/field/lind-*.js`, `img/field/lind/`, `img/field/moss/rilde/` | DEV画質切替などが既存。 | 代表NPCエマから検証、NPC全種を一括置換しない |
| マップ移動/衝突 | `js/field/field-movement.js`, `field-collision.js`, `field-navigation.js` | 移動フレームスケールやマップ座標を既存ロジックが管理。 | カメラ・当たり判定・イベント・SAVEと投影座標を分離して検証 |
| CG | `js/field/rilde-cg.js`, `rilde-ruins-cg.js` | 高精細イベント表示の別経路。 | **変更対象外**。フィールド刷新に伴うCG自動表示や画風変更は禁止 |

## 現状の素材件数（フォルダ分類、PNGのみ）
- `img/field/characters/aidan/`: 62
- `img/field/characters/lou/`: 6
- `img/field/monsters/goblin/`: 20
- `img/field/monsters/moss_slime/`: 6
- `img/field/monsters/forest_bat/`: 4
- `img/field/monsters/leafy_boar/`: 11
- `img/field/lind/npc/`: 90
- `img/field/moss/rilde/`: 220
- `img/field/moss/props/`: 107
- `img/field/moss/art/`: 88
上記は代表的なディレクトリ別集計であり、全760件の内訳ではない。

## 互換性・未解決事項
1. 正式PNGの原本SHA・採用台帳と、各方向の実表示対応表は未照合。元素材の置換・削除は禁止。
2. 2.8頭身の新規静止ドット絵、全方向のanchor/scaleは未制作・未確定。既存2048×1280画像の単純縮小を「正式ドット絵」とみなさない。
3. 25°〜30°の投影を既存マップ座標へ直結すると、衝突・イベント・SAVE復元を壊す可能性がある。描画座標とワールド座標を分離する設計を先行。
4. 既存敵の`art.poses`など戦闘予兆/突進の可読性を単純な静止画化で失わない。状態ごとにパルス・予兆の表現を設計。
5. prefers-reduced-motion、タッチ操作、Android性能、停止時バウンス抑制、非表示時の更新停止を共通QA対象とする。
6. 旧歩行PR #139/#140/#144/#145/#153/#154 は**HOLD**。代替スプライトと描画方式の採用・回帰PASS前に閉じない。

## Phase 2 実装パケット（次工程）
- `js/field/field-sprite-motion.js`（新規）を**純粋計算・副作用なし**で追加し、`sample({kind,moving,time,phase,reducedMotion})`から視覚オフセット/スケールを返す。PC/NPC/敵/妖精の基本モーションを共通化する。
- デフォルトOFFのDEVフラグからのみ試験表示。既存DOM・manifest・移動・当たり判定・SAVEには触れない。
- Nodeテストで停止時0、歩行時周期、妖精浮遊、敵パルス、reduced-motion、非数値入力、位相の決定性を検証。
- 代表3種の新規正式スプライトが揃うまで本番デフォルト切替を行わない。

**監査判定: Phase 1静的調査完了／実機・画質QA NOT_RUN／Phase 2以降未実装。**
