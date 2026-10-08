# リルド村正式制作 v2 — STEP 0 audit / reference inventory

開始基準: `73e02af6b89e236cdb5acd5e21cb422e8b0b8ce5`（fetch後の最新mainと一致）。今回の対象batchはSTEP 0〜3。NPC/Emma生成は後段。

Source audit: 実施。Reference inventory: ZIPで8画像を受領し、すべて目視照合済み。最新main `b0e90369271f868c5bf04ca9bd75f1bdd66c5a6d` をfetchで確認。

**Production status: REFERENCES VERIFIED — STEP 1〜3制作開始。** 添付はreferenceであり、切り抜いて実素材にしない。

## Reference inventory

資料は `docs/art/reference/lind/` に原本のまま保存。`inventory.json` にサイズ・モード・SHA-256を記録。

| 指定資料 | 受領・視覚確認 | 依存STEP |
|---|---|---|
| リルド村 全体マップ（確定版） | 全体マップを確認 | 1〜3、配置・衝突定義・最終統合 |
| 建物／施設素材資料 | 図鑑・宿屋資料で確認 | 2 |
| 宿屋デザイン資料 | 図鑑・宿屋資料で確認 | 2 |
| 農業／畜産施設資料 | 図鑑で確認 | 3 |
| 訓練場資料 | 訓練場資料で確認 | 7 |
| 地形／水辺／自然物資料 | 地形・水辺素材シートで確認 | 1、5、6 |
| 村人NPC参考資料 | 村人スプライトシートで確認 | 9 |
| Emma最新正式キャラクターデザイン資料 | ema.png / emadot.pngを確認 | 10 |

既存 `img/battle/characters/aidan/aidan_reference_sheet.png` は戦闘用Aidan資料であり、村・Emmaの代用referenceにはしない。制作開始前は `img/field/lind/` と正式Emma画像は存在しなかった。新規制作の進捗は `lind-production-batch1.md` へ記録する。

## 動いている実装と再利用する接続点

- Vanilla HTML/CSS/JS。`index.html` の `#world` がフィールドDOMとイベントを保持。`js/game.js` は戦闘結果/ログのbridgeであり、独立したfield engineではない。
- `css/style.css` のworld寸法は2200×1550。地形/建物/木/NPCはCSS・文字・emoji中心のprototype。32×32tile engineは未導入。後の生成素材用の表示寸法と地面collisionはこの座標系に合わせて定義する。
- `camera()` はworldをtranslateしてスクロール。`px/py`、pointer destination、keyboard arrows/WASD、室内 `ipx/ipy` と `dressRoom()` は既存接続点。doorの `data-room=home/inn/shop/elder` を維持する。
- `blockedWorld()` は川x1450〜1630と橋y540〜625の通行判定のみ。建物・木・柵用の正式collisionはまだ存在しない。素材の形状が未確認なので今回推測で追加しない。
- 既存配置: Aidanの家(180,300)、宿(500,270)、道具屋(920,270)、長老宅(1120,125)、井戸(730,550)。確定指示の北東Aidan宅/西shop/北西elderと一致していない。これはprototype座標の事実であり、正式座標の採用ではない。確定マップを受領してから接続先を維持して配置を検討する。
- 川x1450〜1630、橋(1435,540)、訓練場(1540,800)、木人(1630,900)/(1760,930)、Fiona(1710,845)。訓練設備は東側だがprototypeのtraining装飾矩形は川に一部かかる。橋を渡った東側という確定関係を正式化するときに参照画像と足元collisionを照合する。
- `startTraining()` と `dummy1/dummy2.onclick`、FionaのstoryStage条件、join/回復、丘への移動を維持する。外見刷新を理由にイベントを作り直さない。
- 生活NPCは1.8秒ごとの2地点往復。室内表示中・storyStage>=5で停止。農作業/方向別sprite等は現在未実装。既存会話ハンドラを後のactor layerへ移す場合も識別子を維持する。
- 風停止は丘の `hillIndex===10` で `#windVeil` のanimation/opacityを止めるだけ。村全体のgrass/tree/laundry/bird/stone発光を統括する環境systemは未実装。後段STEP 13で水面を止めず風だけ止める状態へ接続する。
- 襲撃は `enterBurningVillage()` / body.villageAttack の既存hide/filter/fire/rubble/smokeとstory flags。正常なイベント導線を保護し、後段に正式damage overlayを追加する。
- Saveは `windbound_oath_v028` キー、version29、`PrologueProgress.serialize/load` のstory/encounter/位置・questとPartyManager/resources。新field metadataで保存形式を書き換えない。
- `js/prologue-dev.js` のDEV_MODE=true、20地点Jump、instant KO、forced criticalとDEV sandbox save保護は維持。
- Battle baseline `73e02af` の5技カットイン/Facing/Banter/Critical/PCサイズ、Raider HP1250とgiant/HUDを保護。今回Battleコード変更なし。

## Emma / story metadata

テキスト設定は [prologue-character-canon.json](../story/prologue-character-canon.json) に保存した。runtimeで読み込まず、NPC会話へ秘密を漏らさないauthoring metadata。

Emmaの老齢・眼鏡・杖・曲がった腰・裁縫・植物刺繍、Fionaの服がEmmaの手作りである点を認識。Emma/Fionaが知るのは森で拾われた事実だけ。Elf救命と実の両親の死はauthor-only truth。Aidan母の病死と騎士への願いも記録。Emmaの2資料を目視確認。老齢・杖・丸眼鏡・まとめ髪・ショールの植物刺繍が設定と一致。原本に複数ポーズがあるが切り抜かない。家の正式割当・生成はSTEP 10まで保留。

## Baseline実行確認

ローカルHTTP配信＋Chromiumで、1280×720 / 844×390 / 390×844を確認。

- map load、2200×1550、camera translate、keyboard移動。
- 川で移動拒否、橋で移動可能。
- training Jumpとdummy interactionでstoryStage1→2、訓練battle表示。
- DEV有効、画像404 0、JS例外0。

これは既存prototypeのsmoke確認であり、未生成の正式素材、全prologue通し、新collision、animals/NPC/EmmaのQAにPASSを付けたものではない。正式画像がないためalpha/anatomy/scale QAは未実施。

## 次のcheckpoint

| STEP | 状態 |
|---|---|
| 0 Source audit | 実施、既存source/実行接続点とstory metadataを記録 |
| 0 Reference inventory | 実施、8画像すべて受領・目視確認・原本保存 |
| 1 Terrain | 7枚制作・仮配置QA済み |
| 2 主要建物 | 10枚制作・仮配置QA済み |
| 3 農業／畜産施設 | 11枚制作・仮配置QA済み |
| 4〜15 | 今回の初期batchでは未着手。EmmaはSTEP 9の縮尺確定後に1点から制作 |

各STEPをstandalone generation→RGBA/目視QA→仮配置→collision/縮尺→3viewport確認→commit/pushの順で進める。reference crop、未確認デザインの独自生成、CSS代替の正式採用はしない。
