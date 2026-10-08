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

## STEP 5 — 自然・小物

14枚を単独生成: 木、低木、白/黄/紫の花群、草/クローバー、小石、大石、切り株、
柵、木箱、樽、飼料、水桶、洗濯物、葉の看板。荷車・干し草・農具はBatch 1を再利用。
全14枚RGBA・完全透明ピクセルあり。明るい背景で全画像を視覚確認し、
背景焼き込みや大きな欠損なし。出力PNGは変更せず、表示時に余白だけ補正。

`motion: wind/static`の分類と`LindFieldEnvironment.setWind()`を用意。
木・低木・草花・洗濯物・看板・既存作物/果樹だけが風の停止対象。
静物と家畜には作用しない。DEV「風ON/OFF」で確認可能。
storyの風停止イベントへの正式接続はSTEP 13。

柵3配置で小屋前の牧区を明示。斜めの柵は6つの足元矩形、木は幹、
洗濯物は2本の支柱のみcollision。草花はwalkable ground decoration。
3画面サイズで画像ロード、家畜の維持、全新collider、風停止、
click/tap/keyboard、review復元をPASS。画像404=0、JS例外=0。
証跡: `qa/lind-batch2/step5-qa.json`と3サイズのスクリーンショット。

## STEP 6 — 川・橋・釣り場

水辺Referenceを使用し、橋・桟橋・釣り竿・籠・葦・河原の小石の6枚を単独生成。
全6枚RGBA、透明ピクセルあり。明るい背景で全画像を視覚確認、不要背景や
大きな欠損なし。水と河岸はBatch 1、木箱はSTEP 5を再利用。

川は東側x1450–1630、橋は従来の中央東側crossing範囲内、釣り場は南東y1325付近。
川の対岸や施設の地域関係を変更しない。直線河川は既存prototype地形の仮配置であり、
Referenceの最終曲線・斜め河岸／seam調整はSTEP 12。

`LindFieldRiver`で橋の床と桟橋の床polygonを定義。
足元4点が床内にあることを確認し、画像の支柱・透過余白を水上歩行領域にしない。
橋を矢印入力で実際に横断、桟橋から水へ踏み出せないことを確認。
将来の釣り人(x1430,y1325)／player(x1475,y1337)用に2立ち位置を確保。
NPCは未制作。仮配置の素材jumpも安全な足場へ移動する。

水流は`lindWaterFlow`、風は`lindFieldWind`で別timeline。
風OFFで草／葦／洗濯物が停止してもwaterのbackground-positionは進行し続ける。
3画面サイズで透明画像・橋横断・水collision・2立ち位置・風停止中water継続・
review復元をPASS。画像404=0、JS例外=0。
証跡: `qa/lind-batch2/step6-qa.json`と3サイズの釣り場画面。

## STEP 7

8枚を単独生成: `train_ground`, `train_shed`, `train_weapon_rack`, `train_target`,
`train_dummy`, `train_post`, `train_gate`, `train_flag_green`。
全8枚RGBA・alpha・完全透明ピクセルあり。明るい背景で全画像を確認し、
不要背景・大きな欠損なし。柵はSTEP 5を再利用。
小さなopen木造小屋・土/草yardであり、要塞や軍事compoundにはしない。
全training objectは川の東側x>=1630。従来の中央橋を渡った土の導線へ接続。

dummyは独立したPNG／collision／44px以上の透明hit area／interaction ID。
`LindFieldTraining`が近接範囲を確認し、クリック・tap・Enterで
`lind-field-interaction`イベントを発行。`reviewOnly:true`付きで、story/saveを進めない。
既存Aidan tutorialを呼び換えたり、新しいfield剣animationを作ったりしない。
後工程のfield/tutorial連携用の受け口。既存live dummy1のtutorialは別途3サイズで再検証PASS。
門は2本の柱のみcollision、中央通路は実際に矢印入力で通行確認。
空のyardはwalkable、旗はwind-driven、dummy/rack/shedはstatic。

3画面サイズでEast配置、門通行、dummy操作、wind、水流、家畜、
collision、画像ロード、review終了時の原位置／flags／save／live river復元をPASS。
証跡: `qa/lind-batch2/step7-qa.json`と3サイズの訓練場画面。

## 最終QA

| 項目 | 結果 |
|---|---|
| 新規素材 | 34枚: STEP 4=6 / STEP 5=14 / STEP 6=6 / STEP 7=8 |
| Alpha / visual | 新規34枚すべてRGBA、実透明ピクセルあり、不要背景・重大欠損なし |
| Animal anatomy | 牛/豚各4脚・1頭・1尾、鶏2脚・1頭、融合・重複顔なし |
| Animal behavior | 独立IDLE/WALK、低速範囲内往復、足元collision、終了時RAF停止 |
| River / water | 東側river、橋の横断、wind OFFでもwater flow継続 |
| Fishing | SE bank、2人用standing spaces、桟橋polygon外の水面侵入禁止 |
| Training | 橋東側、小さなyard、open gate、独立dummyのclick/tap/Enter |
| Collision | 全declared colliderの足元、幹/支柱/柵、yardと門、橋とdockを確認 |
| PC 1280×720 | PASS |
| Mobile landscape 844×390 | PASS（tap destination/dummy/既存tutorial/COMMAND） |
| Mobile portrait 390×844 | PASS（同上） |
| Battle regression | normal/Tainted、Raider、COMMAND、攻撃中DEV撃破、KO固定、Victory、古いtimerの上書きなし |
| Raider | HP1250、巨大sprite、spriteから独立したboss HUD維持 |
| 全登録battle image | 61パスを3サイズのbrowserでロード、すべて成功 |
| Image 404 | 0 |
| JS exceptions / console errors | 0 / 0（最終再検証） |
| Old / invalid runtime references | 0（embedded / numbered / old Lou、literal path監査） |
| Battle source/assets差分 | 0 |
| Batch 1既存PNG差分 | 0 |
| DEV_MODE | true維持 |

最終検証で検出した既存のimplicit `/favicon.ico` 404は、制作済み葉看板PNGを
HTMLのiconに明示して解消。新しいicon画像生成やBattle変更なし。
証跡: `final-source-audit.json`, `final-live-qa.json`, `final-battle-regression.json`。

## Checkpoints

全て通常push、force pushなし。

| 工程 | Commit |
|---|---|
| START | `a5d6f6221cd9aaf15f94a79f4f44b4c6276c6f84` |
| STEP 4 | `cb81bb32827169a1c709f80a372e35ecfd8b5aaf` |
| STEP 5 assets/wind | `e99ba1b003f9d5552d926fd20ff59d0f392824f3` |
| STEP 5 control sync | `c1a4c321637312277e4e69368ef0799eacfddf59` |
| STEP 6 | `37a165354c9310ca4640abf1383aa0cfd446736f` |
| STEP 7 / FINAL | このレポートを含むSTEP 7 checkpoint（Git log参照） |

変更: 新規PNG34枚、`js/field/`のregistry/bounds/reviewと独立actor/environment/
river/training modules、field専用CSS、indexのfield読み込みとicon参照、監査/manifest/QA文書。
削除ファイルなし。Battle、ストーリー、save、Emma/NPC、正式主人公field素材は変更なし。

## 維持事項・警告

Battle source/assets/actor state、DEV_MODE=trueを維持。
Batch 1の高解像度生成素材・仮配置・未統合のmapという制約を継承。
正式32×32タイル化／seamless境界、roof分離、story event再配置は今回の完了対象外。
家畜のWALKは2ポーズの簡易歩行で、高度なAIや多方向フルanimationではない。
釣り人／playerのstanding spotsは確保済みだが、NPC追加は今回未実施。
正式field character/NPC scaleはSTEP 9以降、dummyの実tutorial接続はSTEP 12。
各画像のmode・alpha数・寸法・SHA: `lind-asset-audit.json`。
制作出典・工程・reviewOnly: `lind-production-manifest.json`。

判定: **PASS WITH WARNINGS**。制作・仮配置・基礎動作のQAはPASS、最終map統合と
正式character scaleは後工程。STEP 8以降へ進まず **PLAYER QA READY** で停止。
