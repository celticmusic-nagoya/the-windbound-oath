# PLAYER-WALK-POLISH-01 v2 — Phase A監査

基準main: `e63780543d7ba1719a39a2f68b9924dc6d5b3933`（PR #127）。案件全体は **PARTIAL**。Phase Aは監査・制作仕様の提出まで。Phase Bの修正版は未制作、ディレクター採用未実施、Phase C/Dは未着手。周期だけの変更で足の交互運動をPASSにしない。

既存の画像・素材参照・周期・移動速度・当たり判定・SAVE・戦闘・シナリオは変更していない。エイダン左右180を維持。上下150等は比較案であり未採用。Claudeをこのセッションから起動する実行手段はなく、以下はCodex監査とClaude向け引継ぎ仕様である。GitHubの引継ぎ投稿自体がClaudeを自動起動するものではない。

## 実装・全コマの監査範囲

名目8方向に対し、実ゲームでは10歩行bank・52PNGを使用する。Fionaの左右には正横6コマと斜め移動用4コマが別にあり、後者を監査対象から落とさない。Fiona idle4枚も別途比較した。

|人物・方向|実使用bank|コマ|現行周期|基準300world/s時の1周|判定・対応|
|---|---|---:|---:|---:|---|
|エイダン左|side6 / fix01の既存参照|6|180|0.600秒|PR127の周期・素材を保護。今回差替え対象外|
|エイダン右|side6 / fix01の既存参照|6|180|0.600秒|同上|
|エイダン上|walk_up|6|90|0.300秒|支持足の注釈なし。靴底露出・中間姿勢の連続性を制作で確認|
|エイダン下|walk_down|6|90|0.300秒|同じ側の足の強調が連続。反対足の接地・通過姿勢を明示する候補が必要|
|フィオナ上|walk_up|4|90|0.300秒|01/03は逆側の靴底が見える。全コマ非交互とは判定しない。中立姿勢・体形の整合を修復|
|フィオナ下|walk_down|4|90|0.300秒|01/03とも画面右側の足が前。反対足の位相不足|
|フィオナ左|side_left / walk_left|6 /4|90|0.300秒|正横:反対足・杖欠落。斜め:03で視点・身体の不連続|
|フィオナ右|side_right / walk_right|6 /4|90|0.300秒|正横:反対足・杖欠落。斜め:支持足同定と対応位相の確認が必要|

Fionaは追従移動距離で位相が進み、加減速により実時間の周期が変わる。DEVは基準300world/sで比較する。実追従とDEVの瞬間速度が常に同じとは扱わない。

## 根拠と原因の分離

- [エイダン24コマ・接地の確実性・原本履歴](evidence/player-walk-polish01/aidan/PHASE-A-FRAMES.md)。6ファイルあるだけでは6つの正しい歩行位相を証明しない。静止画で接地と上げ足を区別できない箇所は未確定と記録した。
- [エイダン上下全コマと足元拡大](evidence/player-walk-polish01/aidan/vertical-contact.png)。切断された足先を新たに断定せず、靴底露出・同側の強調・02→03/06→01の連続性を制作対象とする。
- [フィオナ監査](evidence/player-walk-polish01/fiona/FIONA_AUDIT.md)、[全32枚の個別判定](evidence/player-walk-polish01/fiona/PER_FRAME.md)、[原本参照SHA](evidence/player-walk-polish01/fiona/source-inventory.json)。profile全12枚に杖が描かれていない。キャンバス外クリッピングではない。
- [フィオナ正面比較](evidence/player-walk-polish01/fiona/fiona_walk_down-full.png)、[正横比較](evidence/player-walk-polish01/fiona/fiona_side_right-full.png)、[背面足元](evidence/player-walk-polish01/fiona/fiona_walk_up-feet.png)。背面は逆足が見えるため、正面・正横と同じ欠損判定をしない。
- [左右profile登録差](evidence/player-walk-polish01/fiona/mirror-registration.json):反転した前景は148/149pxの移動後に一致する。共通anchorに対し14.8〜14.9worldの登録差がある。これを接地足中心と取り違えず、骨盤/root・地面基準で候補を校正する。
- 既存の[再納品依頼A2](../art/redelivery_requests.md)と[当時の割当README](../art/reference/characters/walk_delivery_20261011b/README.md)にも逆足位相不足の記録がある。ただし当時の全状態を現在全方向の判定に転用していない。
- AidanHeadingは斜め移動に正面/背面bankを再利用。Fionaは正横と斜めのbankを切替。現在DEVはFiona正横だけを左右選択で表示するため、Phase Cでは斜めbankも見落とさない検証手段が必要。

## 制作とコードの境界

**素材側**:左右の解剖学的な足・支持足・遊脚が追跡できる接地/通過ポーズ、Fionaの杖・服・頭身・顔の一貫性、ループ中の輪郭とroot整合。単なる並べ替え、減速、足だけの平行移動、全体反転では不足位相を作れない。

**コード側（承認後）**:採用されたbank/枚数/anchorの登録、必要最小限の位相・bob/接地校正、方向別の距離周期、DEVで全実使用bankの検証、終了時の後片付け。移動速度・collision・追従アルゴリズム・SAVEは変更しない。候補PNGを本編の参照先へ接続しない。

## Phase B向け具体仕様

[Claude制作仕様](../art/PLAYER-WALK-POLISH-01_CLAUDE.md)を正本とする。まずAidan上下12枚＋Fiona4方向24枚＝36候補PNGを提案。Fiona斜め用2bankを残す場合は追加12枚の候補、または採用済み正面/背面bankの再利用方針について別途採用判断が必要。**48枚や6コマの採用を確定したものではない**。

周期120/150/180の0.400/0.500/0.600秒比較は、両足の正しい位相がそろってから行う。現行90は比較基準として残す。採用済みAidan左右180を変更しない。支持足と通過姿勢を確認せず、全方向へ180をコピーしない。

## QAと未実施の区別

- Phase A metadata/alpha監査:8方向/10bank/52歩行PNG。SHA・canvas・登録・透明外縁を記録。[機械可読一覧](evidence/player-walk-polish01/inventory.json)。透明外縁PASSは足の内部形状・接地品質のPASSではない。
- 正式259PNGおよび既存PNGの原本保護確認。[保護結果](evidence/player-walk-polish01/protection.json)。本編差分なし。
- Phase A独立レビュー:PRの固定HEADに対する判定を引継ぎコメントへ記録する。
- 修復後の歩行完成QA、修正前後比較、通常移動/SAVE/CONTINUE/戦闘回帰、Android実機、候補採用: **NOT_RUN**。画像候補と採用がまだないため、この監査をPhase D PASSの代用にしない。

本PRは監査・仕様・比較資料・読み取り専用監査ツールのみ。本編変更・mainマージ・Pages更新は本フェーズでは実施しない。
