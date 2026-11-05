# PLAYER-WALK-ARM-02 — 本番統合

2026-11-05ディレクター正式採用・mainマージ・Pages自動公開承認に基づく統合。基準main `74d0401192f8417d9433253767c30b6b540af454`、専用branch `feature/player-walk-arm-02-production`。

## 登録

- 01（現行）→05（ARM-02）→02（ARM-02）→06（接地修復済み）。周期90、bob25%、06全身補正0、アンカー(1024,1230)、scale .0625、移動速度は維持。
- 正式05：`img/field/characters/aidan/down4/arm02/aidan_walk_down_05_arm02.png`、SHA `6c857b4cbf1459df48ecd305b41ffa7f1b7b98a1458b6d2243a8c50c94e17bad`。
- 正式02：`img/field/characters/aidan/down4/arm02/aidan_walk_down_02_arm02.png`、SHA `614bdeffb8c09b3dbb7e0b688cea21efdfc7b68ccdeea0ddf53694f0bc13824f`。
- PR #144 `95e5563032095790e7a6887c74fa466f44a0bead` の該当候補を無加工で複製。PR #145（`996eb165fe6089ab92334b53274a4b27db395e88`）の独立視覚・技術QA PASSを参照。
- 旧01/05/02と旧06、接地修復06、正式259PNGは保持。新規2枚以外の既存1829PNGは変更しない。候補ディレクトリ・比較UI・DEVコード・試作画像は取り込まない。

本番コードは `AidanFieldAssets` の05/02のURL2箇所とindexの該当JSキャッシュキーだけ更新。共有歩行・移動・衝突・SAVE・他方向・Fiona・シナリオ・既存DEVは変更しない。斜め下は従来どおり下向き絵を共用する。

採用マニフェスト `img/field/characters/aidan/down4/adopted-walk.json` は現在4枚のSHAとARM-02承認/出典/独立QAを記録。前回の採用リストと根拠は履歴に保持し、接地06の旧来出典PR139も保持する。中央素材台帳の新2枚をAPPROVED、AndroidはUNVERIFIED。原本の承認状態を一括変更しない。

## QA

作者実行の本番回帰6/6 PASS：m62通常下歩行、m58左右180、m55味方/敵/NPC共通DEV、SAVE/CONTINUE、素材台帳監査、m49正式SHA。Node17本PASS（歩行テスト11サブテスト）。PC1920×1080、縦390×844、横844×390。

通常NEW GAMEとキー/タッチ移動で、実PNG参照・順序・約.300秒周期・90world実移動差・quarter-bob・壁停止・停止再開/反転・SAVE状態保護を検証。本番05/02がPR144とバイト一致、頭/脚/反対腕が旧原本と一致することを独立に確認。原本1829PNG不変、正式259SHA一致。DEV/試作混入0、共有エンジン/SAVE/data変更0。

初期静的レビューで採用履歴の生成が浅いコピーになり旧05/02リストも更新される点を検出。公開前に基準mainの旧リストへ復元し、履歴SHAの回帰assertを追加した。現在の採用ファイルとは別リストを保持する。動作や画像を変更する修正ではない。最終固定HEADは実装者以外の独立QAを実行し、PRコメントへ記録する。上記作者QAと独立QAは区別する。

[証拠](evidence/player-walk-arm-02-production/)にrunnerログ、Node出力、原本保護、実フィールド動画・画像、可逆圧縮raw＋SHAを保存。過去のPR144/145の画像・コードは上書きしない。

## 統合と公開

ディレクター承認に従い独立QA PASS後、最新main/固定head/競合/必須チェック/rollback refを確認して通常マージする。Pages完了後、公開index・素材定義JS・採用マニフェスト・実画像とmerge SHAを照合し、結果をPRへ記録する。異常を未実施PASSとして扱わない。

軽微な残存事項（既知・採用承認済み）：05→02の白い裏地差、05手袋下の局所しわ、02→06の短い近似保持。今回の統合で新たな画像加工・追加調整はしない。

## Android実機（未実施）

公開後、CONTINUEで移動可能なフィールドへ入り、下歩行→停止/再開→方向転換→縦横回転を確認。新規確認はNEW GAME→自宅→冒頭会話終了（既存SAVEは上書きしない）。既存プレイでSAVE→再起動→CONTINUEも確認する。実機QAはディレクターが実施し、問題があれば別修正タスクへ分離する。
