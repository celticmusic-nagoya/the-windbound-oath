# PLAYER-WALK-POLISH-01 v2 — Claude Phase B制作仕様

STATUS: READY_FOR_CLAUDE（仕様引継ぎ。Claude実行済みではない）
BASE: main `e63780543d7ba1719a39a2f68b9924dc6d5b3933`
OWNER: Claude（候補制作） / Codex（監査・承認後の実装） / director（採用・Android判断）
ADOPTION: 未採用。既存PNG上書き、本編参照変更、mainマージはこの制作依頼では行わない。

## 所有ファイルの分離

- Claude: `assets/candidates/player-walk-polish01/aidan/**`、同`fiona/**`、専用の新規生成/抽出スクリプトと候補QA証拠。別の専用featureブランチからPR提出する。Codexの監査PRと同じファイルを編集しない。
- Codex: `js/field/*`、`js/dev/*`、index/cache、監査・統合テスト。ただし現在は監査だけ。Phase Cは具体的な候補パス/SHAのディレクター承認後。
- 既存の正式259PNG、元シート、全旧フレーム、Aidan左右のPR127素材・周期180、battle/story/SAVE/collision/movementは保護する。

## 入力・全コマ監査

[現状監査](../qa/PLAYER-WALK-POLISH-01.md)とその証拠を確認する。

- Aidan:`js/field/aidan-field-assets.js`のwalk_up/down各01..06。原本2048×1280、anchor[1024,1230]、scale.0625。既存の顔・髪・剣・外套・装飾・色・頭身を一致させる。既存front/backシートは参照用。既存side6/fix01（現行の採用区分を維持）を修正対象へ拡大しない。
- Fiona:`js/field/fiona-field-assets.js`の32枚と原本参照台帳。原本1280×832、anchor[640,790]、scale.1。顔・髪・花飾り・人間の耳・衣装・ブーツ・杖のデザイン/持ち手を同じキャラクターとして維持。
- 後期Fiona6コマシートの原ファイルはmainに見つからない。旧raw_NN.webpは半分サイズの参考画像。未承認・低解像度の別デザイン素材を黙って代用しない。復元可能な元画素の回収と、不足する反対足ポーズの新規制作を区別する。
- 正横で現在消えている杖を、正面/背面・idleの既存設定と整合するよう描く。スカートの下に足だけを貼り付けず、膝・裾・隠れ方・腕・重心のつながりを制作する。

## 枚数・bank案（採用前）

第一batchは各方向6コマ案: Aidan up/down=12PNG、Fiona up/down/正横left/right=24PNG、合計36PNG。

|候補bank|候補ファイル例|枚数案|
|---|---|---:|
|Aidan上/下|`aidan/frames/aidan_walk_up_01.png` 等|各6|
|Fiona上/下|`fiona/frames/fiona_walk_up_01.png` 等|各6|
|Fiona正横左/右|`fiona/frames/fiona_side_left_01.png` 等|各6|

現行Fionaの斜め用walk_left/right各4枚も通常プレイで使われる。第一batchだけでこの2bankの不連続をCLOSEDにしない。継続使用する場合は同じ条件で各6コマ、追加12PNGを第二batchとして提案する。別の採用済みbankへ統一する案は、方向の見え方が変わるためCodex/ディレクターへ別案として返す。無断で描画方向を置換しない。必要なidle差分も理由・枚数を提案し、未承認の追加を正式素材へ混ぜない。

6コマを必須の固定結論にはしない。4/8等が適切なら、両足の接地と中間姿勢が見える根拠・追加量を提案してから納品仕様を確定する。

## 歩行位相

6コマ案は以下を基準に、実際の絵で成立するよう調整する。

1. 左足接地・右足後方
2. 左支持・右足通過
3. 左支持後半・右足前方スイング
4. 右足接地・左足後方
5. 右支持・左足通過
6. 右支持後半・左足前方スイング →1

全コマに解剖学的なleft/right、support/swing、heel/toe/contact、pelvis/rootを注釈する。正面では人物左足は画面右、背面では人物左足は画面左。横向きは近脚/遠脚が解剖学的にどちらか明記する。陰影だけの役割交換やwhole-image mirrorを逆足の接地として数えない。静止画で見えない支持足は推測でPASSにしない。

## 登録・透過・比較

- 既存canvas/anchor/scaleを維持する案を優先。変更が必要なら新しい候補metadataとして提案し、Codexへ影響を返す。旧PNGへ直接書き込まない。
- 素材ごとに最下部alphaや最も突き出た杖へ合わせて身体を自動拡縮しない。人体の骨盤/root・頭部・地面で同じ縮尺を校正する。
- Fiona左右の現行14.8–14.9world登録差を候補へ引き継がない。杖・髪・裾を含めても画面端の透明余白を確保し、背景・市松・地面線を焼き込まない。
- 各旧/新を同じcamera/scale/groundで並べた全身・ネイティブ足元・黒/白/市松比較、1倍ループ、末尾→先頭、停止姿勢と方向転換の比較を納品する。
- 現行90と候補120/150/180の比較は提案値。基準300world/sで.300/.400/.500/.600秒/周。Fiona実追従は加減速する。速度やSAVE値を書き換えて見栄えを作らない。Aidan左右180は変更しない。

## 納品と採用ゲート

`manifest.json`: source/outputパス・SHA256・解像度・target_bank・direction・index・anatomical脚/支持脚・contact/root座標・画像加工/生成手順・比較QA・既知課題・`approval_status: CANDIDATE_NOT_ADOPTED`。

現物がないoutput SHAや採用状態を先に埋めない。最初の候補PRに全コマと比較資料を入れ、directorへ外観判断を渡す。承認は具体的なファイル/SHAを対象とする。候補の生成・PR提出は正式採用ではない。

採用後、Codexが登録・DEV全実使用bank・通常フィールド・SAVE/CONTINUE・回帰・259SHA・独立QAを実施する。Android実機の最終判断はdirector。新素材の採用前に本編参照や描画周期を先行変更しない。
