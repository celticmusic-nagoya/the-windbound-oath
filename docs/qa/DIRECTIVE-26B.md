# DIRECTIVE-26B — 序盤報酬4箇所修正

**PASS（P6-REWARD-01）。R01/R02/R03/R04すべて実給付・重複防止・SAVE/LOAD検証済み。** 全経路連続プレイ・総合Android実機の完了判定は26C以降へ分離する。

基準main `ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3`（PR100）。[25A監査](DIRECTIVE-25A.md)・[26A修復](DIRECTIVE-26A.md)と過去証拠は変更せず、当時の報酬FAILを履歴として保全。

## 実給付

| ID | 対象 | 既存API | 同じfresh-game内の実測 | 判定 |
|---|---|---|---|---|
| R01 | 家のタンス | Inventory.grant({potion:1}) | きずぐすり4→5 | PASS |
| R02 | 家の壺 | Inventory.grant({gold:3}) | 0→3G | PASS |
| R03 | 風船依頼 | Inventory.grant({potion:2}) | きずぐすり5→7 | PASS |
| R04 | 迷子猫依頼 | Inventory.grant({antidote:2}) | 毒消し0→2 | PASS |

元の取得・受注・発見・完了条件内で付与し、同じ同期呼出内で既存flagを確定する。新しい報酬システム・flag・イベント条件は追加しない。新旧の家の取得口は同じdrawer/pot flagを共有し、どちらを先に使っても追加は1回のみ。受注前の風船/猫調査には給付しない。台詞・数量・選択肢・Phase5表情指定は維持。

## 毒消しは保持のみ

`ItemData`に`antidote`という最小の消耗品データを追加。既存の`battleItems`任意キーとInventory APIで保持・一覧表示する。**SAVE v30／prologue v2／legacyEvents v1、保存構造は変更しない。** 解毒・状態異常・新しい回復効果・戦闘コマンドは追加しない。説明は「現在は使用できない。」。

既存の戦闘APIは任意の所持IDを受け、potion以外をFiona MP回復へ流せるため、毒消しに限るearly returnを`item`／`applyItem`入口へ各1行追加した。対象選択・在庫減算・HP/MP・ターン処理の前に拒否する。通常戦闘とRaiderの双方で無変化を検証し、既存potion45回復／ether12MP回復も実測した。その他の戦闘処理・数値はbyte単位で不変。

旧SAVEが任意キーantidoteを持たない場合、LOAD成功後に現セッションの同キーだけ除去し0個にする。LOAD失敗・世代取消時には除去しない。明示0個、所持2個のSAVEはその値を復元する。NEW GAMEは新アイテムの在庫だけ0へ初期化し、元SAVEを書き換えない。既存の他資源の初期化方針は変更しない。

## 旧SAVEと取得履歴

- 取得後の再調査・別取得口・map再訪：増加0。
- SAVE→同一セッションLOAD→再調査：数量と既存flag維持、増加0。
- タイトルからcold CONTINUE→再訪：数量とflag維持、増加0。
- 旧SAVEの完了済みflagと所持数は保存値のまま。実給付がなかった可能性を推測して補償しない。
- legacyEventsなしの旧SAVEは、既存のunknown制限／quest完了推定規則をそのまま使用。drawer/potのunknownを受取済みの証明と読み替えない。flagリセットなし。
- LOAD／NEW GAMEは元のlocalStorage SAVE bytesを保持。プレイヤーの明示SAVE以外で補正書込しない。

## QA — PASS

[集計](evidence/directive-26b/summary.json)、[実給付・重複・保存の96チェック](evidence/directive-26b/reward-browser.json)。390×844、844×390、1920×1080で実本編の登録hook／legacy handler／本物のInventory・SAVE・CONTINUEを実行。状態設定・map直接再訪を含むモジュールQAであり、全経路通常プレイ完走と混同しない。legacy handlerのproximityは実DOM距離で確認。

- 修正前と同じ未変更の`playable_audit_25a.py`も**FAILS0**。4報酬の実数差分がPASSへ変化した[原プローブ結果](evidence/directive-26b/original-25a-probe.json)を保存。
- Node原版**14/14**＋追加の報酬・互換性・無効果**13ケース**PASS（計15suite）。失敗／supersede LOAD、旧キー欠落／0／2個、同一tab NEW GAME、新旧取得口cross、通常／Raiderの使用拒否を検証。[全ログ/testSHA](evidence/directive-26b/node/results.json)。
- 26A故障注入**8/8検出PASS**＋厳密抽出契約PASS。故障は専用processのメモリ読取だけへ注入し、原版exit1・INJECTED印・固有エラーを要求。[結果](evidence/directive-26b/faults/negative-results.json)。
- 回帰**13種類すべてPASS、計16実行**。初回13本後、毒消し使用ガードを追加した最終版で報酬／m16／m53を再実行。重複を13種類へ数え上げない。[初回](evidence/directive-26b/initial-regressions/results.json)／[最終](evidence/directive-26b/final-regressions/results.json)。ブラウザ直列、Git履歴付きexact HEAD snapshotを使用。
- SAVE lifecycle、shop、equipment、normal/Raider battle、エマ/老人/農婦クエスト、115ページ表情/m53、瞬き・timer・reduced-motion/m45、正式SHA/m49/m51、26A素材原版の鮮度・台帳・参照検査PASS。
- 正式259PNGは固定SHA一致。採用台帳・PortraitRegistry/Blink/renderer、過去QA証拠は不変。既存runtime1456ファイルのうち**1452不変／承認範囲4ファイルのみ変更**。[保護証拠](evidence/directive-26b/protection.json)。

m53の会話behavior SHA `4d9c203b00d45ac245a369350b8fe910bf4e2a1164e5cb492aa82bf7b1c10114`は不変。index全制御hashは正当な付与・互換性変更により`c6fa5ff607f98c0e64ebdad8a1185cff0ca52e4ade61b6db7ddda1835f513640`へ更新。単にhashを緩めず、新reward QAで4ファイルの正確な許可差分（6grant、保持用定義、欠落キー／新規開始処理、毒消し専用拒否、cacheキー）だけを逆適用すると基準mainへbyte完全一致することを検証する。原文・条件・既存アイテム定義・戦闘処理の意図しない変更はFAIL。

## 変更と公開

製品変更はindex、rilde-village、item-data、battle-action-targetsのみ。script cacheキー3件を更新し、新定義と保持専用guardの旧cache混在を防ぐ。テスト・証拠・P6計画・引継ぎ以外の変更なし。

独立exact-head QA、rollback refのremote SHA読み戻し、最新main/PRhead/競合/必須checkを満たして通常merge。PagesのActions成功と公開ファイル/main byte一致をmerge後に別回収し最終報告する。公開設定変更なし。Android実機はNOT_RUN。

次工程：**DIRECTIVE-26C — 全経路連続QA**。Phase6の他の未完成事項を、本件4報酬の修正だけで全体PASSへ変更しない。
