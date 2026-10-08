# Lind Village Production — Batch 2 (STEP 4–7)

開始main: `a5d6f6221cd9aaf15f94a79f4f44b4c6276c6f84`。
Batch 1と同じDEV素材仮配置を使用。本マップ・イベント座標への正式統合はSTEP 12。
STEP 8以降、field主人公、Emma、村人NPCの制作は行わない。

## STEP 4 — 家畜

6枚のstandalone PNG: `animals/{cow,pig,chicken}_{idle,walk}.png`。
各idleは素材図鑑を参照して単独制作。承認したidle自体をwalkのReferenceに
使用し、個体の顔・模様・体格を維持。sheetからのcropなし。
生成PNGは無加工で配置。全画像RGBA、alphaと完全透明ピクセルあり。
明るい背景へ合成したQA画像で、黒・白・市松背景の焼き込みなしを確認。

ANATOMY QA: 牛・豚の各idle/walkは頭1、胴体1、脚4、尾1。
牛の角2・耳2、豚の耳2・巻き尾1。鶏は頭1・胴体1・脚2・自然な翼／羽尾。
重複顔、複数頭、融合した別個体、不自然な追加脚、端での欠損なし。

`LindFieldAnimals` / `FieldAnimal`はbattleから独立。
各actorのIDLE/WALK、左右反転、休止時間、低速移動、矩形活動範囲、足元collisionを管理。
牛5px/s・休止6秒、豚7px/s・4秒、鶏9px/s・3秒。
歩行は独立したidle/walk画像を交互表示。二枚を事前読み込みし、表示切替だけで動作。
仮配置を閉じるとRAFを取り消し、live fieldでは動かない。
家畜の範囲は各小屋前の牧区。正式な柵配置はSTEP 5、最終map連携はSTEP 12。

1280×720 / 844×390 / 390×844: 実RAFの停止→歩行、画像表示、
活動範囲内の往復、足元collision、click/tap・矢印移動、仮配置終了時停止、
元座標・room・story flags・localStorage復元を確認。
各viewportの画像404=0、JS例外=0。証跡: `qa/lind-batch2/step4-qa.json`。

Scaleは既存34×44px CSS playerを仮の比較対象とした牛56px幅、豚43px、鶏24px。
正式field character制作前なので最終scale確定とはしない。

## STEP 5–7

未着手。各前工程のQAとcheckpoint push完了後に進める。

## 維持事項・警告

Battle source/assets/actor state、DEV_MODE=trueを維持。
Batch 1の高解像度生成素材・仮配置・未統合のmapという制約を継承。
正式32×32タイル化／seamless境界、roof分離、story event再配置は今回の完了対象外。
各画像のmode・alpha数・寸法・SHA: `lind-asset-audit.json`。
制作出典・工程・reviewOnly: `lind-production-manifest.json`。
